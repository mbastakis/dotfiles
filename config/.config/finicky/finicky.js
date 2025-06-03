export default {
  defaultBrowser: "Vivaldi",
  options: {
    checkForUpdates: true,
    logRequests: true,
  },
  handlers: [
    {
      // Telekom related URLs - open in Microsoft Edge
      match: [
        "*yam-united*",
        "*yam-united.telekom.com/*",
      ],
      browser: "Microsoft Edge",
    }
  ]
};