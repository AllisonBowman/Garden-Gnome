Pod::Spec.new do |s|
  s.name           = 'PlantSpeech'
  s.version        = '1.0.0'
  s.summary        = 'On-device continuous speech recognition for describing a garden aloud'
  s.description    = 'Wraps SFSpeechRecognizer + AVAudioEngine for hands-free, on-device dictation while walking a garden. Prefers on-device recognition so it works with no signal.'
  s.author         = 'Garden Gnome'
  s.homepage       = 'https://github.com/AllisonBowman/Garden-Gnome'
  s.license        = { :type => 'MIT' }
  s.source         = { :git => '' }

  # Matches PlantId and ExpoModulesCore's SDK 57 minimum. Speech and AVFoundation
  # are both long-standing frameworks, so nothing here needs weak linking — the
  # feature gates on authorization and on-device support at runtime instead.
  s.platforms      = { :ios => '16.4' }
  s.swift_version  = '5.9'
  s.static_framework = true

  s.dependency 'ExpoModulesCore'

  s.frameworks = 'Speech', 'AVFoundation'

  s.pod_target_xcconfig = {
    'DEFINES_MODULE' => 'YES',
    'SWIFT_COMPILATION_MODE' => 'wholemodule'
  }

  s.source_files = '**/*.{h,m,mm,swift,hpp,cpp}'
end
