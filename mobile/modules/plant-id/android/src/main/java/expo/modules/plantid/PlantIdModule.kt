package expo.modules.plantid

import android.graphics.BitmapFactory
import android.net.Uri
import expo.modules.kotlin.Promise
import expo.modules.kotlin.exception.CodedException
import expo.modules.kotlin.modules.Module
import expo.modules.kotlin.modules.ModuleDefinition

// On-device plant identification for Android via ML Kit GenAI Prompt API
// (AICore-backed Gemini Nano). No network call for inference.
//
// ⚠️ BUILD/TEST CAVEAT: not compiled on this machine (no Android SDK). The ML
// Kit GenAI Prompt API is new; verify the class/method surface below
// (GenerativeModel / PromptRequest / feature status) against the shipping SDK.
// Gemini Nano only runs on AICore-capable devices (currently newer flagships) —
// unsupported devices return isAvailable() == false and the JS layer falls
// back to manual species search.

import com.google.mlkit.genai.common.FeatureStatus
import com.google.mlkit.genai.common.DownloadCallback
import com.google.mlkit.genai.prompt.Generation
import com.google.mlkit.genai.prompt.GenerativeModel
import com.google.mlkit.genai.prompt.PromptRequest

class PlantIdModule : Module() {
  private val model: GenerativeModel by lazy { Generation.getClient() }

  override fun definition() = ModuleDefinition {
    Name("PlantId")

    AsyncFunction("isAvailable") { promise: Promise ->
      try {
        model.checkFeatureStatus()
          .addOnSuccessListener { status ->
            promise.resolve(status == FeatureStatus.AVAILABLE || status == FeatureStatus.DOWNLOADABLE)
          }
          .addOnFailureListener { promise.resolve(false) }
      } catch (e: Throwable) {
        // Missing AICore / unsupported device / API not present.
        promise.resolve(false)
      }
    }

    AsyncFunction("identify") { imageUri: String, prompt: String, promise: Promise ->
      try {
        model.checkFeatureStatus()
          .addOnSuccessListener { status ->
            when (status) {
              FeatureStatus.UNAVAILABLE ->
                promise.reject(CodedException("Gemini Nano is not available on this device."))
              FeatureStatus.DOWNLOADABLE, FeatureStatus.DOWNLOADING ->
                downloadThenInfer(imageUri, prompt, promise)
              FeatureStatus.AVAILABLE ->
                runInference(imageUri, prompt, promise)
              else ->
                promise.reject(CodedException("Unknown feature status: $status"))
            }
          }
          .addOnFailureListener { e -> promise.reject(CodedException("Feature status check failed", e)) }
      } catch (e: Throwable) {
        promise.reject(CodedException("On-device model unavailable", e))
      }
    }
  }

  private fun downloadThenInfer(imageUri: String, prompt: String, promise: Promise) {
    model.downloadFeature(object : DownloadCallback {
      override fun onDownloadCompleted() = runInference(imageUri, prompt, promise)
      override fun onDownloadFailed(e: Exception) =
        promise.reject(CodedException("Model download failed", e))
      override fun onDownloadStarted(bytesToDownload: Long) {}
      override fun onDownloadProgress(totalBytesDownloaded: Long) {}
    })
  }

  private fun runInference(imageUri: String, prompt: String, promise: Promise) {
    val ctx = appContext.reactContext
      ?: return promise.reject(CodedException("No Android context"))
    val bitmap = ctx.contentResolver.openInputStream(Uri.parse(imageUri)).use {
      BitmapFactory.decodeStream(it)
    } ?: return promise.reject(CodedException("Could not read the selected image."))

    val instructions =
      "You identify houseplant species. Respond with ONLY the single most likely " +
      "species: common name, plus scientific name in parentheses if confident. No extra words."
    val request = PromptRequest.builder("$instructions\n$prompt")
      .addImage(bitmap)
      .build()

    model.runInference(request)
      .addOnSuccessListener { result -> promise.resolve(result.text) }
      .addOnFailureListener { e -> promise.reject(CodedException("Inference failed", e)) }
  }
}
