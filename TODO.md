# TODO: VSCode Extensions Installation Script
CREATE data/scripts/install_vscode_extensions.sh
This script will install the VSCode extensions listed in: data/vscode_extensions/
data/vscode_extensions is a directory containing many extensions with a .vsix file.
The script should:
USE the vsce command to install each extension.
The script should be executable.
This script should be added in the config: config/config/dotfiles/config.yaml at the app tool.

#TODO: Fix Rsync Command
When running rsync with: dotfiles rsync install data/claude we get the error:
dotfiles rsync install data/claude 
Installing rsync items: data/claude
❌ 
Error: failed to sync some sources: data/claude: rsync failed: exit status 23
Output: Transfer starting: 8 files
rsync(83189): warning: /Users/A200407315/./Library/Application Support/CallHistoryTransactions: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Application Support/com.apple.sharedfilelist: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Application Support/Knowledge: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Application Support/com.apple.TCC: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Application Support/FileProvider: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Application Support/AddressBook: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Application Support/FaceTime: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Application Support/DifferentialPrivacy: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Application Support/com.apple.avfoundation/Frecents: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Application Support/com.apple.avfoundation: not empty, cannot delete
rsync(83189): warning: /Users/A200407315/./Library/Application Support/CallHistoryDB: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Application Support: not empty, cannot delete
rsync(83189): warning: /Users/A200407315/./Library/Assistant/SiriVocabulary: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Assistant: not empty, cannot delete
rsync(83189): warning: /Users/A200407315/./Library/Daemon Containers: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Autosave Information: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/IdentityServices: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Calendars: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Messages: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/HomeKit: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Sharing: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/com.apple.aiml.instrumentation: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Mail: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Trial: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/AppleMediaServices: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/DuetExpertCenter: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Accounts: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Safari: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Biome: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/IntelligencePlatform: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Shortcuts: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Suggestions: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Weather: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.stocks-news: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.photolibraryd.private: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.feedback: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.siri.inference: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.swtransparency: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.coreservices.useractivityd: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.accessibility.voicebanking: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.siri.referenceResolution: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.stocks: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.usernoted: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.VoiceMemos.shared: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.secure-control-center-preferences: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.chronod: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/com.apple.MailPersonaStorage: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.private.translation: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.appstoreagent: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.portrait.BackgroundReplacement: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.amsondevicestoraged: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.SiriTTS: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.iBooks: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.calendar: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.newsd: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.ip.redirects: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.siri.userfeedbacklearning: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.gamecenter: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.tips: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.tv.sharedcontainer: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.spotlight: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.studentd: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.ManagedSettings: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.sharingd: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.printtool: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.news: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.mobileslideshow.PhotosFileProvider: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.scopedbookmarkagent: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.weather: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/com.apple.systempreferences.cache: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.feedbacklogger: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.siri.remembers: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.notes: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/com.apple.stickersd.group: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.UserNotifications: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.tipsnext: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/com.apple.messages: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.Safari.SandboxBroker: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.transparency: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.reminders: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.mail: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/com.apple.bird: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.DeviceActivity: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.replayd: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/com.apple.Home.group: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.iCloudDrive: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.energykit: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/com.apple.PreviewLegacySignaturesConversion: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.replicatord: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.Photos.PhotosFileProvider: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.AppleSpell: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.mlhost: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.PegasusConfiguration: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/group.com.apple.shortcuts: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers/com.apple.MessagesLegacyTransferArchive: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Group Containers: not empty, cannot delete
rsync(83189): warning: /Users/A200407315/./Library/Containers/com.apple.VoiceMemos: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Containers/com.apple.archiveutility: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Containers/com.apple.Maps/Data/Maps: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Containers/com.apple.Maps/Data: not empty, cannot delete
rsync(83189): warning: /Users/A200407315/./Library/Containers/com.apple.Maps: not empty, cannot delete
rsync(83189): warning: /Users/A200407315/./Library/Containers/com.apple.Home: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Containers/com.apple.Safari: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Containers/com.apple.mail: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Containers/com.apple.MobileSMS: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Containers/com.apple.Notes: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Containers/com.apple.corerecents.recentsd/Data/Library/Recents: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Containers/com.apple.corerecents.recentsd/Data/Library: not empty, cannot delete
rsync(83189): warning: /Users/A200407315/./Library/Containers/com.apple.corerecents.recentsd/Data: not empty, cannot delete
rsync(83189): warning: /Users/A200407315/./Library/Containers/com.apple.corerecents.recentsd: not empty, cannot delete
rsync(83189): warning: /Users/A200407315/./Library/Containers/com.apple.stocks: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Containers/com.apple.Safari.WebApp: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Containers: not empty, cannot delete
rsync(83189): warning: /Users/A200407315/./Library/ContainerManager: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/PersonalizationPortrait: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Metadata/CoreSpotlight: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Metadata/com.apple.IntelligentSuggestions: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Metadata: not empty, cannot delete
rsync(83189): warning: /Users/A200407315/./Library/Cookies: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/CoreFollowUp: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/StatusKit: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/DoNotDisturb: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Caches/com.apple.HomeKit: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Caches/CloudKit: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Caches/com.apple.Safari: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Caches/com.apple.containermanagerd: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Caches/FamilyCircle: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Caches/com.apple.homed: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Caches/com.apple.ap.adprivacyd: unreadable directory: Operation not permitted
rsync(83189): warning: /Users/A200407315/./Library/Caches: not empty, cannot delete
rsync(83189): warning: /Users/A200407315/./Library: not empty, cannot delete
rsync(83189): warning: /Users/A200407315/./.Trash: unreadable directory: Operation not permitted
./

sent 416 bytes  received 26 bytes  7 bytes/sec
total size is 14164  speedup is 32.05
rsync(83188): warning: child 83189 exited with status 23
---
This should not be happening since in the config we specify that the target of data/claude is "~"
The rsync is done correctly since I can see the files in the target directory. But the error is still there.
Also in dotfiles tui the status of rsync is "failed" but the files are there.


#TODO: Add ai_docs and specs to the config
The ai_docs and specs directories are not included in the config.yaml file.
They exist in the config/ai_docs and config/specs directories.
They should be added to the config.yaml file in the stow tool.

#TODO: dotfiles TUI main menu order issue
The main menu of the dotfiles TUI is changing the order of the tools: stow, rsync, homebrew, apps, npm, uv
every time I run the dotfiles TUI, the order of the tools is different.
REFLECT on this issue and try to find a solution.
CORRECT order should be: stow, rsync, homebrew, apps, npm, uv as defined in the config.yaml file.

#
