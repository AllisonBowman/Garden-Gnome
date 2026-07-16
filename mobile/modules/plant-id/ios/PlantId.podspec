Pod::Spec.new do |s|
  s.name           = 'PlantId'
  s.version        = '1.0.0'
  s.summary        = 'On-device plant identification via Apple Foundation Models + Vision'
  s.description    = 'Bridges Apple Foundation Models (iOS 26+) and Vision for on-device, network-free plant species identification. Degrades gracefully on older devices.'
  s.author         = 'Garden Gnome'
  s.homepage       = 'https://github.com/AllisonBowman/Garden-Gnome'
  s.license        = { :type => 'MIT' }
  s.source         = { :git => '' }

  # NOTE: 16.4 matches ExpoModulesCore's minimum for SDK 57 — CocoaPods
  # refuses to resolve a pod pinned below its dependency's platform. This
  # does NOT gate the iOS-26 Foundation Models feature: that usage is
  # @available-guarded and the framework is weak-linked below, so pre-26
  # devices simply report isAvailable() == false rather than failing.
  s.platforms      = { :ios => '16.4' }
  s.swift_version  = '5.9'
  s.static_framework = true

  s.dependency 'ExpoModulesCore'

  s.pod_target_xcconfig = {
    'DEFINES_MODULE' => 'YES',
    'SWIFT_COMPILATION_MODE' => 'wholemodule',
    # Weak-link the iOS 26 framework so it's optional at runtime.
    'OTHER_LDFLAGS' => '-weak_framework FoundationModels'
  }

  s.source_files = '**/*.{h,m,mm,swift,hpp,cpp}'
end
