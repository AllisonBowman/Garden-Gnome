import ExpoModulesCore
import Foundation
import UIKit

// On-device plant identification for iOS.
//
// Design: iOS 26's Foundation Models is a *text* model, so photo→species-name
// is done in two on-device steps with no network at any point:
//   1. Vision (VNClassifyImageRequest) extracts visual labels from the photo.
//   2. Foundation Models reasons over those labels + the caller's prompt and
//      returns a single most-likely species name.
//
// ⚠️ BUILD/TEST CAVEAT: this requires the Xcode 26 SDK to compile and an
// Apple-Intelligence-capable device (iOS 26+) to run. It has not been compiled
// on this machine (no macOS/Xcode). Verify the Foundation Models API surface
// (LanguageModelSession init and `respond(to:)`) against the shipping SDK when
// building — Apple has iterated on these signatures.

#if canImport(FoundationModels)
import FoundationModels
#endif
#if canImport(Vision)
import Vision
#endif

struct PlantIdError: LocalizedError {
  let message: String
  var errorDescription: String? { message }
}

public class PlantIdModule: Module {
  public func definition() -> ModuleDefinition {
    Name("PlantId")

    AsyncFunction("isAvailable") { () -> Bool in
      PlantIdModule.foundationModelsAvailable()
    }

    AsyncFunction("identify") { (imageUri: String, prompt: String) async throws -> String in
      guard PlantIdModule.foundationModelsAvailable() else {
        throw PlantIdError(message: "Apple Intelligence / Foundation Models is not available on this device.")
      }
      #if canImport(FoundationModels)
      if #available(iOS 26.0, *) {
        // 1) On-device perception.
        let labels = try PlantIdModule.classifyImage(uri: imageUri)
        // 2) On-device language: constrain the model to a single species name.
        let session = LanguageModelSession(instructions: """
          You identify houseplant species from visual labels. Respond with ONLY \
          the single most likely species: its common name, and scientific name \
          in parentheses if you are confident. No explanation, no extra words.
          """)
        let composed = "\(prompt)\nVisual labels from the photo: \(labels.joined(separator: ", "))"
        let response = try await session.respond(to: composed)
        return response.content
      }
      #endif
      throw PlantIdError(message: "Foundation Models requires iOS 26 or newer.")
    }

    // Text-only generation over the same on-device model (used by the gnome
    // voice). The caller supplies the full prompt; no instructions added here.
    AsyncFunction("generate") { (prompt: String) async throws -> String in
      guard PlantIdModule.foundationModelsAvailable() else {
        throw PlantIdError(message: "Apple Intelligence / Foundation Models is not available on this device.")
      }
      #if canImport(FoundationModels)
      if #available(iOS 26.0, *) {
        let session = LanguageModelSession()
        let response = try await session.respond(to: prompt)
        return response.content
      }
      #endif
      throw PlantIdError(message: "Foundation Models requires iOS 26 or newer.")
    }
  }

  private static func foundationModelsAvailable() -> Bool {
    #if canImport(FoundationModels)
    if #available(iOS 26.0, *) {
      // .available means the model is present AND Apple Intelligence is enabled
      // and not restricted by region/hardware/Settings.
      if case .available = SystemLanguageModel.default.availability {
        return true
      }
    }
    #endif
    return false
  }

  @available(iOS 26.0, *)
  private static func classifyImage(uri: String) throws -> [String] {
    guard let url = URL(string: uri),
          let data = try? Data(contentsOf: url),
          let cg = UIImage(data: data)?.cgImage else {
      throw PlantIdError(message: "Could not read the selected image.")
    }
    #if canImport(Vision)
    let request = VNClassifyImageRequest()
    try VNImageRequestHandler(cgImage: cg, options: [:]).perform([request])
    let labels = (request.results ?? [])
      .filter { $0.confidence > 0.1 }
      .prefix(8)
      .map { $0.identifier }
    return Array(labels)
    #else
    return []
    #endif
  }
}
