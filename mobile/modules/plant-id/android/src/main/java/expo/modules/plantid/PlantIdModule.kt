package expo.modules.plantid

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import expo.modules.kotlin.exception.CodedException
import expo.modules.kotlin.modules.Module
import expo.modules.kotlin.modules.ModuleDefinition

// ML Kit GenAI Prompt API (AICore-backed Gemini Nano, on-device). Multimodal:
// image + text -> text. No network call for inference.
//
// ⚠️ Not compiled on this machine (no Android SDK). Gemini Nano runs only on
// AICore-capable devices (currently newer flagships) — unsupported devices
// return isAvailable() == false and the JS layer falls back to manual search.
import com.google.mlkit.genai.common.*
import com.google.mlkit.genai.prompt.*
import kotlinx.coroutines.flow.*

class PlantIdModule : Module() {
  // Generation.getClient() creates the on-device generative model client.
  private val model by lazy { Generation.getClient() }

  private val instructions =
    "You identify houseplant species. Respond with ONLY the single most likely " +
    "species: common name, plus scientific name in parentheses if confident. No extra words."

  override fun definition() = ModuleDefinition {
    Name("PlantId")

    AsyncFunction("isAvailable") Coroutine {
      try {
        val status = model.checkStatus()
        status == FeatureStatus.AVAILABLE || status == FeatureStatus.DOWNLOADABLE
      } catch (e: Throwable) {
        // Missing AICore / unsupported device / API not present.
        false
      }
    }

    AsyncFunction("identify") Coroutine { imageUri: String, prompt: String ->
      when (model.checkStatus()) {
        FeatureStatus.UNAVAILABLE ->
          throw CodedException("Gemini Nano is not available on this device.")
        FeatureStatus.DOWNLOADABLE, FeatureStatus.DOWNLOADING ->
          // One-time on-device model download before first use.
          model.download().collect { }
        FeatureStatus.AVAILABLE -> {}
        else -> {}
      }

      val bitmap = loadBitmap(imageUri)
        ?: throw CodedException("Could not read the selected image.")

      val response = model.generateContent(
        generateContentRequest(
          ImagePart(bitmap),
          TextPart("$instructions\n$prompt"),
        )
      )
      response.candidates.firstOrNull()?.text
        ?: throw CodedException("The model returned no result.")
    }
  }

  private fun loadBitmap(imageUri: String): Bitmap? {
    val ctx = appContext.reactContext ?: return null
    return ctx.contentResolver.openInputStream(Uri.parse(imageUri)).use {
      BitmapFactory.decodeStream(it)
    }
  }
}
