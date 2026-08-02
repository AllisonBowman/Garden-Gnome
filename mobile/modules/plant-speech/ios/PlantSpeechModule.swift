import ExpoModulesCore
import Foundation
import Speech
import AVFoundation

// Hands-free dictation for describing a garden out loud.
//
// Why this exists rather than the keyboard's dictation key: walking a bed with
// muddy hands, you want to keep talking — naming one plant, moving on, naming
// the next — without tapping between each. This keeps a recognition session
// open and streams partial text as it hears it.
//
// On-device by preference. `requiresOnDeviceRecognition` is set whenever the
// recognizer reports it's supported, because gardens and allotments routinely
// have no signal and because the alternative ships audio of someone's garden
// to a server. If the device can't do it locally we fall back to the system
// default rather than failing, and the JS side is told which one is in use so
// the app can say so honestly.
//
// ⚠️ BUILD/TEST CAVEAT: like modules/plant-id, this has not been compiled on
// this machine. SFSpeechRecognizer and AVAudioEngine are stable APIs, but
// verify against the shipping SDK on the first build.

struct PlantSpeechError: LocalizedError {
  let message: String
  var errorDescription: String? { message }
}

public class PlantSpeechModule: Module {
  private var recognizer: SFSpeechRecognizer?
  private var request: SFSpeechAudioBufferRecognitionRequest?
  private var task: SFSpeechRecognitionTask?
  /// Whether the caretaker still wants to be heard. Distinguishes a
  /// hand-off between phrases from a real stop, so one doesn't look like
  /// the other.
  private var wantsToListen = false
  private let audioEngine = AVAudioEngine()

  public func definition() -> ModuleDefinition {
    Name("PlantSpeech")

    // onTranscript fires repeatedly as speech is heard: `text` is the whole
    // utterance so far, `isFinal` marks the end of a phrase. onSpeechError
    // reports a session that stopped for a reason the user should know about.
    Events("onTranscript", "onSpeechError")

    AsyncFunction("isAvailable") { () -> Bool in
      guard let r = SFSpeechRecognizer(locale: Locale.current) ?? SFSpeechRecognizer() else {
        return false
      }
      return r.isAvailable
    }

    /// Whether recognition can run without a network round-trip on this device.
    AsyncFunction("supportsOnDevice") { () -> Bool in
      guard let r = SFSpeechRecognizer(locale: Locale.current) ?? SFSpeechRecognizer() else {
        return false
      }
      return r.supportsOnDeviceRecognition
    }

    /// Asks for speech recognition and microphone access. Returns true only if
    /// both were granted — either one alone is useless.
    AsyncFunction("requestPermission") { (promise: Promise) in
      SFSpeechRecognizer.requestAuthorization { status in
        guard status == .authorized else {
          promise.resolve(false)
          return
        }
        // AVAudioApplication arrived in iOS 17. This pod's floor is 16.4 (that
        // is ExpoModulesCore's minimum for SDK 57), so the call it replaced is
        // still the only one available at the bottom of the supported range.
        if #available(iOS 17.0, *) {
          AVAudioApplication.requestRecordPermission { granted in
            promise.resolve(granted)
          }
        } else {
          AVAudioSession.sharedInstance().requestRecordPermission { granted in
            promise.resolve(granted)
          }
        }
      }
    }

    AsyncFunction("start") { () throws -> Bool in
      try self.startListening()
    }

    AsyncFunction("stop") { () -> Void in
      self.stopListening()
    }

    // A recognition session holding the microphone open is not something to
    // leave running because a screen went away.
    OnDestroy {
      self.stopListening()
    }
  }

  /// Begins a continuous session. Returns true when recognition is running
  /// on-device, false when it fell back to the system default.
  private func startListening() throws -> Bool {
    stopListening()

    guard SFSpeechRecognizer.authorizationStatus() == .authorized else {
      throw PlantSpeechError(message: "Speech recognition hasn't been allowed for PlantAdvocate.")
    }
    guard let recognizer = SFSpeechRecognizer(locale: Locale.current) ?? SFSpeechRecognizer(),
          recognizer.isAvailable else {
      throw PlantSpeechError(message: "Speech recognition isn't available on this device right now.")
    }
    self.recognizer = recognizer

    // The simulator has no working audio input. Starting the engine there does
    // not fail politely: AURemoteIO's RPC to the audio server times out and
    // AudioToolbox calls abort(), killing the app from a C++ frame that no
    // Swift error handling can reach. Refusing up front is the only way to
    // keep the crash from happening, and a clear message beats a dead app.
    #if targetEnvironment(simulator)
    throw PlantSpeechError(
      message: "Listening needs a real device — the simulator has no microphone to open.")
    #else
    let session = AVAudioSession.sharedInstance()
    try session.setCategory(.record, mode: .measurement, options: .duckOthers)
    try session.setActive(true, options: .notifyOthersOnDeactivation)

    // Same reasoning on hardware: if there is no input route, starting the
    // engine can abort rather than return. Ask first.
    guard session.isInputAvailable else {
      throw PlantSpeechError(
        message: "No microphone is available right now.")
    }

    let onDevice = recognizer.supportsOnDeviceRecognition
    self.wantsToListen = true

    let input = audioEngine.inputNode
    input.removeTap(onBus: 0)
    // Prepare before reading the format: the input node can still be reporting
    // a zeroed format immediately after the session goes active.
    audioEngine.prepare()
    let format = input.inputFormat(forBus: 0)

    // installTap validates this with an Objective-C assertion, and an
    // Objective-C exception is not catchable from Swift — an invalid format
    // terminates the whole app instead of returning an error. So check it here
    // and fail like a normal function. Simulators routinely report a zeroed
    // format, and so does a device whose microphone was taken by another app
    // between the permission grant and this line.
    guard format.sampleRate > 0, format.channelCount > 0 else {
      stopListening()
      throw PlantSpeechError(
        message: "This device isn't offering a usable microphone right now.")
    }

    // Feed whichever request is current rather than one captured here: a
    // finished phrase swaps in a new request underneath, and a tap pinned to
    // the old one would go on filling a request nobody is reading.
    input.installTap(onBus: 0, bufferSize: 1024, format: format) { [weak self] buffer, _ in
      self?.request?.append(buffer)
    }

    try audioEngine.start()
    beginSegment(on: recognizer, onDevice: onDevice)

    return onDevice
    #endif
  }

  /// Start one recognition segment.
  ///
  /// A recognition task ENDS when it reports a final result — it does not carry
  /// on to the next sentence. Someone walking a bed naming plants pauses
  /// constantly, and each pause finishes a phrase, so a single task would go
  /// deaf after the first plant. Each finished phrase therefore starts a fresh
  /// segment while the audio engine and its tap keep running underneath.
  private func beginSegment(on recognizer: SFSpeechRecognizer, onDevice: Bool) {
    let request = SFSpeechAudioBufferRecognitionRequest()
    request.shouldReportPartialResults = true
    request.requiresOnDeviceRecognition = onDevice
    self.request = request

    self.task = recognizer.recognitionTask(with: request) { [weak self] result, error in
      guard let self else { return }

      if let result {
        self.sendEvent("onTranscript", [
          "text": result.bestTranscription.formattedString,
          "isFinal": result.isFinal,
        ])
        if result.isFinal, self.wantsToListen {
          // Hand off to a new segment. The caller keeps the text of the phrase
          // that just ended; this one starts empty.
          self.task = nil
          self.request = nil
          self.beginSegment(on: recognizer, onDevice: onDevice)
        }
        return
      }

      if let error {
        // Cancellation is how stop() and each hand-off end a task; it is not
        // something the caretaker needs to hear about.
        let ns = error as NSError
        let cancelled = ns.domain == "kLSRErrorDomain" || ns.code == 203 || ns.code == 216
        if self.wantsToListen && !cancelled {
          self.sendEvent("onSpeechError", ["message": error.localizedDescription])
          self.stopListening()
        }
      }
    }
  }

  private func stopListening() {
    wantsToListen = false
    // Touching inputNode at all spins up the audio unit, which is exactly what
    // aborts on a simulator — so on that platform there is nothing to tear down
    // because nothing was ever started.
    #if !targetEnvironment(simulator)
    if audioEngine.isRunning {
      audioEngine.stop()
    }
    audioEngine.inputNode.removeTap(onBus: 0)
    try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
    #endif
    request?.endAudio()
    task?.cancel()
    task = nil
    request = nil
  }
}
