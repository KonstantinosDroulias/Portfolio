customgifts.gr sells promotional gifts to businesses. Like most WooCommerce stores, it grew one plugin at a time: a page builder for the layout, an SEO plugin, a production calendar, custom fields, a CRM connector, a search plugin, a cache plugin. Each one solved a real problem. Together they made a store that was slow, hard to update and hard to reason about.

This autumn I moved it to its own theme and replaced most of those plugins with modules I write and maintain myself. Here's how I did it without breaking a live store that takes real orders.

## Why bother

The goal was never to write more code. It was to have fewer moving parts I don't understand.

- **Updates changed behaviour** I depended on, usually on a Friday.
- **I paid for features** and used a small part of them.
- **Data was spread** across tables and meta keys, each plugin with its own idea of how to store it.

> A plugin you didn't write is a decision someone else keeps making for your business.

## Leave the page builder first

The old layout was built with Divi. Its shortcodes were everywhere: in pages, in product descriptions, even in the SEO descriptions. The new theme is plain PHP templates and one stylesheet, built around what the store actually needs: price tables by quantity, a colour × size grid for apparel, add-ons and quotes.

Static pages like About, Shipping and Payment were rebuilt as theme templates that read their details live from the store settings. Change a bank account or a shipping rate once, and every page shows it.

## Move the data before you switch anything off

Every replacement followed the same order:

1. Build the new module next to the old plugin.
2. Import the old plugin's data into the new structure.
3. Compare the two until the numbers match.
4. Only then switch the old plugin off.

For SEO, that meant importing every title, description, primary category, template and redirect from the old plugin, and sending the old sitemap addresses to the new one with a 301. The production calendar was rebuilt as a module of the shop's own plugin, and the same jobs had to show up on the new board before the old one went away.

```php
$old = get_post_meta( $product_id, '_old_plugin_options', true );

if ( $old ) {
    update_post_meta( $product_id, '_shop_options', map_options( $old ) );
}
```

Keeping each mapping in one function meant I could run it on a copy as many times as I needed.

## Check what users and Google see

Before and after the switch I crawled the store and compared the results:

- **139 addresses** kept the same URL and the same status code.
- **102 products** kept the same prices and order data.
- The production board showed **the same 41 jobs**.

There was also a full backup of the database, themes and plugins, and a one-line rollback script, so turning back would have taken minutes. It wasn't needed.

## What I'd do differently

Start with the plugin that touches the fewest orders. The first replacement teaches you how your own code should be structured, and it's better to learn that on something small than on checkout.
