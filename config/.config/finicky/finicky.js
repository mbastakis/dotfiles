export default {
  defaultBrowser: "Vivaldi",
  
  rewrite: [
    {
      // Example: Force HTTPS for all URLs
      match: ({url}) => url.protocol === "http",
      url: ({url}) => {
        return {...url, protocol: "https"};
      }
    },
    {
      // Example: Remove tracking parameters from URLs
      match: () => true,
      url: ({url}) => {
        const removeKeysStartingWith = ["utm_", "uta_", "fbclid", "gclid"];
        const search = url.search
          .split("&")
          .map((parameter) => parameter.split("="))
          .filter(([key]) => !removeKeysStartingWith.some((startingWith) => 
            key.startsWith(startingWith) || key === startingWith));
        
        return {
          ...url,
          search: search.map((parameter) => parameter.join("=")).join("&"),
        };
      }
    }
  ],
  
  handlers: [
    {
      // Try to use an already opened browser instance
      match: ({opener}) => opener && opener.name !== undefined,
      browser: ({opener}) => {
        const supportedBrowsers = ["Vivaldi", "Microsoft Edge", "Google Chrome", "Firefox"];
        if (opener && supportedBrowsers.includes(opener.name)) {
          console.log(`Opening URL in existing ${opener.name} instance`);
          return opener.name;
        }
        return "Vivaldi";
      }
    },
    {
      match: [
        // "example.com/*",  // Example domain
        // "*.microsoft.com/*",  // Example with wildcard for subdomains
        // ({ url }) => url.host.includes("office")  // Example with function matcher
      ],
      browser: "Microsoft Edge"
    },
    {
      match: () => true,
      browser: "Vivaldi"
    }
  ],
  
  options: {
    hideIcon: false
  }
}