# Finicky Configuration Documentation

## Overview

[Finicky](https://github.com/johnste/finicky) is a macOS application that allows you to set up rules to determine which browser opens for specific URLs. This configuration file makes Vivaldi your default browser while enabling more advanced browser control.

## Features

This configuration includes:

1. **Vivaldi as Default Browser**: All links will open in Vivaldi unless specified otherwise.

2. **Browser Instance Reuse**: Links will open in the same browser that triggers them when possible. For example, if you click a link in Vivaldi, it opens in Vivaldi instead of creating a new window/instance.

3. **Browser-Specific URL Routing**: Directs specific URLs to open in Microsoft Edge (template included).

4. **URL Rewriting**:
   - Forces HTTPS for all URLs
   - Removes common tracking parameters

## Customization Guide

### Adding Sites to Open in Edge

Edit the `finicky.js` file and modify the section under "Open specific domains in Microsoft Edge". Uncomment and customize the match patterns:

```javascript
// TEMPLATE: Open specific domains in Microsoft Edge
match: [
  "example.com/*",  // Specific domain
  "*.microsoft.com/*",  // All subdomains of microsoft.com
  ({ url }) => url.host.includes("office")  // URLs containing "office"
],
browser: "Microsoft Edge"
```

### Match Patterns

Finicky supports several ways to match URLs:

1. **String patterns**: `"example.com/*"` - Simple glob patterns
2. **Regular expressions**: `/example\.com\/specific-path/`
3. **Functions**: `({ url }) => url.host.includes("example")`

### Advanced Matching

You can match based on more than just the URL:

```javascript
match: ({ url, opener }) =>
  url.host.includes("docs.google.com") && opener.name === "Slack",
browser: "Google Chrome"
```

This would open Google Docs links in Chrome, but only when clicked from Slack.

### Browser Options

To specify browser profiles:

```javascript
browser: {
  name: "Microsoft Edge",
  profile: "Work Profile"
}
```

### Installation

1. Install Finicky: `brew install --cask finicky`
2. Place the configuration file at `~/.finicky.js`
3. Start Finicky and set it as your default browser in macOS System Settings

## Troubleshooting

- If links don't open in the expected browser, check the Finicky logs in Console.app
- Verify that the browser names match exactly with what macOS recognizes
- Try simpler rules first and build up complexity

## Additional Resources

- [Finicky GitHub Repository](https://github.com/johnste/finicky)
- [Configuration Ideas Wiki](https://github.com/johnste/finicky/wiki/Configuration-ideas)
