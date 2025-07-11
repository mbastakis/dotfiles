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
        "*yo-digital.com/*",
        "*.telekom.com*",
        "*.telekom.de*",
        "*telekom.net*",
      ],
      browser: "Google Chrome",
    }
  ]
};
