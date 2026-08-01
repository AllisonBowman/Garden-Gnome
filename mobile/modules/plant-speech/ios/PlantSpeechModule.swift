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
        AVAudioApplication.requestRecordPermission { granted in
          promise.resolve(granted)
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

    let session = AVAudioSession.sharedInstance()
    try session.setCategory(.record, mode: .measurement, options: .duckOthers)
    try session.setActive(true, options: .notifyOthersOnDeactivation)

    let request = SFSpeechAudioBufferRecognitionRequest()
    // Keep the session open across pauses — someone walking a bed stops
    // talking between plants, and that shouldn't end the recording.
    request.shouldReportPartialResults = true
    let onDevice = recognizer.supportsOnDeviceRecognition
    request.requiresOnDeviceRecognition = onDevice
    self.request = request

    let input = audioEngine.inputNode
    let format = input.outputFormat(forBus: 0)
    input.removeTap(onBus: 0)
    input.installTap(onBus: 0, bufferSize: 1024, format: format) { [weak request] buffer, _ in
      request?.append(buffer)
    }

    audioEngine.prepare()
    try audioEngine.start()

    self.task = recognizer.recognitionTask(with: request) { [weak self] result, error in
      guard let self else { return }
      if let result {
        self.sendEvent("onTranscript", [
          "text": result.bestTranscription.formattedString,
          "isFinal": result.isFinal,
        ])
      }
      if let error {
        // A cancelled task is how stop() ends things; it isn't worth reporting.
        let ns = error as NSError
        let cancelled = ns.domain == "kLSRErrorDomain" || ns.code == 203 || ns.code == 216
        if !cancelled {
          self.sendEvent("onSpeechError", ["message": error.localizedDescription])
        }
        self.stopListening()
      }
    }

    return onDevice
  }

  private func stopListening() {
    if audioEngine.isRunning {
      audioEngine.stop()
    }
    audioEngine.inputNode.removeTap(onBus: 0)
    request?.endAudio()
    task?.cancel()
    task = nil
    request = nil
    try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
  }
}
