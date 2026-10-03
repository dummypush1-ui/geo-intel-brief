# Inline report styling

The report sanitizer keeps bounded decorative inline CSS, including solid colors,
linear gradients, spacing, typography and borders. It is a resource/execution
boundary, not a guarantee of text visibility or color contrast. White text on a
white background can still be unreadable.

CSS dimensions, overflow, opacity, text alpha/RGBA colors and negative margins
are omitted. Font sizes use 8-99px/pt. Existing HTML table width attributes remain;
the preserved 700px report table overflows a 390px browser viewport and is not
claimed to be mobile-responsive.

A `background:linear-gradient(...)` declaration gets a solid color fallback.
A `background-image` gradient does not automatically get that fallback. Email
clients can omit gradients. Rendering has been checked in Chrome only, not a
matrix of email clients.

Styles are bounded to 64 declarations and 4000 output characters. No remote CSS,
URL-based CSS resources, scripting expressions, custom variables, positioning or
animation is allowed. This design support does not enable delivery or change
sender, recipient, schedule, collector or storage settings.
