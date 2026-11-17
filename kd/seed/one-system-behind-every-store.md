For a long time every store I worked on had its own way of doing things. A different theme, a different set of plugins, a different spreadsheet for production. Each one started as a quick fix, and each quick fix made sense on its own. Put together, they made a business that was hard to see in one place.

So I started building an ERP that sits in the middle, and turned the stores into what they should be: shop windows that talk to it.

## The problem with one-off sites

The family business runs several online stores: printing, DTF transfers, promotional gifts, custom hats. Over the years they drifted apart. One store kept orders in WooCommerce, another needed a manual export, production lived in a calendar plugin on one site and in someone's head on another.

None of this is unusual. It's what happens when you build fast for real customers. But it means:

- the same product is priced in several places, and the prices slowly disagree;
- nobody can answer "what do we have to print today?" without opening four tabs;
- every new feature has to be built again for each store.

## The hub

The ERP is a Django REST API with a React front end. It owns the things that should exist once: orders, products, pricing rules, suppliers, staff and permissions. Each store runs a small connector that syncs with it, so an order placed on any site lands in the same place, in the same shape.

> A website is only one part of a business system. The useful part is what happens after the customer clicks "order".

Background jobs handle the slow work: syncing stores, sending emails, reading the shared inbox. When something breaks, a health endpoint says which part is down, and an alert reaches my phone before a customer notices.

## One theme, many stores

The second half of the change was on the WordPress side. Instead of a separate theme per store, there is now one shared parent theme and one set of ERP plugins, with a thin child theme per brand for colours, fonts and a few templates.

Updates go out through a private update channel, the same way any plugin updates in WordPress. I bump a version, publish a package, and each store pulls it from its dashboard. No copying files over by hand, no "which version is on which site?".

The smallest store, the custom hats shop, is the test bed. New features land there first, on real orders, before they reach the bigger stores.

## What changed in practice

- One place to look at the day's orders across every store.
- Features like quotes, product add-ons and print-ready order sheets are built once and switched on per store.
- Prices and product data come from the same source, so they stop drifting.
- A new store is mostly a child theme and a connection, not a new project.

## What I'd tell myself at the start

Start with the data, not the screens. The first version of the ERP had nice pages and a messy model underneath, and every new store made it worse. The rewrite began with the questions "what is an order here?" and "who is allowed to change it?", and the screens became easy after that.

And keep the stores boring. The more logic lives in the hub, the less each shop has to know, and the less there is to break.
