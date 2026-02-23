"""
Seed script to populate the database with initial data:
- Admin user
- Categories (Rings, Necklaces, Bracelets, Earrings)
- Sample products with ORIAL design
- Sample discount code
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, User, Category, Product, Discount, SiteSettings, ProductImage, NavigationItem

app = create_app()

def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("✓ Database tables created")

        # Admin user
        admin = User(
            first_name='Eleanor',
            last_name='Marsh',
            email='admin@orial.com',
            is_admin=True,
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)

        # Regular test user
        user = User(
            first_name='Jane',
            last_name='Doe',
            email='jane@example.com',
            is_active=True
        )
        user.set_password('test123')
        db.session.add(user)
        print("✓ Users created (admin@orial.com / admin123)")

        # Categories
        cats = [
            Category(name='Rings', slug='rings', display_order=1, description='Engagement rings, eternity bands, and statement pieces.', is_active=True),
            Category(name='Necklaces', slug='necklaces', display_order=2, description='Pendants, chains, and layering necklaces.', is_active=True),
            Category(name='Bracelets', slug='bracelets', display_order=3, description='Bangles, cuffs, and tennis bracelets.', is_active=True),
            Category(name='Earrings', slug='earrings', display_order=4, description='Studs, drops, and hoops in gold and platinum.', is_active=True),
        ]
        for c in cats:
            db.session.add(c)
        db.session.flush()
        print("✓ Categories created")

        ring_cat = cats[0]
        neck_cat = cats[1]
        brac_cat = cats[2]
        ear_cat  = cats[3]

        # Products
        products = [
            Product(
                name='Rose Bloom Ring',
                slug='rose-bloom-ring',
                subtitle='18K Rose Gold · Pink Diamond',
                description='A stunning solitaire ring featuring a naturally blush-toned diamond set in hand-polished 18K rose gold. Each stone is individually selected for its unique hue.',
                price=2850,
                original_price=3200,
                stock=8,
                category=ring_cat,
                badge='Bestseller',
                badge_color='rose',
                is_featured=True,
                is_active=True,
                material='18K Rose Gold',
                gemstone='Natural Pink Diamond (0.8ct)',
                weight='3.2g',
                sku='ORR-001'
            ),
            Product(
                name='Celestial Solitaire',
                slug='celestial-solitaire',
                subtitle='Platinum · D-Colour Diamond',
                description='Our flagship solitaire, crafted in platinum with a D-colour, excellent-cut diamond. The setting is deliberately minimal to let the stone speak for itself.',
                price=5400,
                stock=4,
                category=ring_cat,
                badge='New',
                badge_color='black',
                is_featured=True,
                is_active=True,
                material='Platinum 950',
                gemstone='D-Colour Diamond (1.2ct)',
                weight='4.1g',
                sku='ORR-002'
            ),
            Product(
                name='Sapphire Eternity Band',
                slug='sapphire-eternity-band',
                subtitle='18K White Gold · Blue Sapphire',
                description='A full eternity band featuring perfectly matched blue sapphires in a grain setting. The sapphires are sourced exclusively from Sri Lanka.',
                price=3750,
                stock=6,
                category=ring_cat,
                badge=None,
                is_featured=True,
                is_active=True,
                material='18K White Gold',
                gemstone='Ceylon Blue Sapphires',
                sku='ORR-003'
            ),
            Product(
                name='Stella Drop Necklace',
                slug='stella-drop-necklace',
                subtitle='18K Yellow Gold · Emerald',
                description='A delicate emerald drop suspended on a fine 18K yellow gold chain. The emerald is Zambian origin, prized for its deep, velvety green colour.',
                price=1950,
                stock=12,
                category=neck_cat,
                badge='Limited',
                badge_color='black',
                is_featured=True,
                is_active=True,
                material='18K Yellow Gold',
                gemstone='Zambian Emerald (0.6ct)',
                sku='ORN-001'
            ),
            Product(
                name='Aria Chain Necklace',
                slug='aria-chain-necklace',
                subtitle='18K Rose Gold · Diamond Pavé',
                description='A versatile everyday necklace with a diamond pavé pendant. The chain length is adjustable, making it perfect for layering.',
                price=1320,
                original_price=1500,
                stock=15,
                category=neck_cat,
                badge='Sale',
                badge_color='rose',
                is_featured=False,
                is_active=True,
                material='18K Rose Gold',
                gemstone='Diamond Pavé',
                sku='ORN-002'
            ),
            Product(
                name='Luna Tennis Bracelet',
                slug='luna-tennis-bracelet',
                subtitle='18K White Gold · Diamond',
                description='A classic tennis bracelet featuring a continuous line of round brilliant diamonds. The secure box clasp ensures it stays put throughout the day.',
                price=4200,
                stock=5,
                category=brac_cat,
                badge='New',
                badge_color='black',
                is_featured=True,
                is_active=True,
                material='18K White Gold',
                gemstone='Round Brilliant Diamonds (3.2ct total)',
                sku='ORB-001'
            ),
            Product(
                name='Soleil Bangle',
                slug='soleil-bangle',
                subtitle='22K Yellow Gold · Hammered',
                description='A handcrafted bangle in high-karat yellow gold with a delicately hammered finish that catches the light beautifully.',
                price=2100,
                stock=9,
                category=brac_cat,
                is_featured=False,
                is_active=True,
                material='22K Yellow Gold',
                sku='ORB-002'
            ),
            Product(
                name='Dusk Drop Earrings',
                slug='dusk-drop-earrings',
                subtitle='18K Rose Gold · Ruby',
                description='Statement drop earrings featuring Burmese rubies in a delicate rose gold setting. The stones are heat-treated only, prized by collectors worldwide.',
                price=3100,
                stock=7,
                category=ear_cat,
                badge='Bestseller',
                badge_color='rose',
                is_featured=True,
                is_active=True,
                material='18K Rose Gold',
                gemstone='Burmese Ruby',
                sku='ORE-001'
            ),
            Product(
                name='Lune Diamond Studs',
                slug='lune-diamond-studs',
                subtitle='Platinum · D-Colour Diamonds',
                description='A timeless pair of diamond stud earrings. Each stone is GIA-certified, D-colour, VVS1 clarity — the highest standard of diamond purity.',
                price=2750,
                stock=10,
                category=ear_cat,
                badge=None,
                is_featured=True,
                is_active=True,
                material='Platinum 950',
                gemstone='D-Colour VVS1 Diamonds (0.5ct each)',
                sku='ORE-002'
            ),
        ]
        for p in products:
            db.session.add(p)
        print(f"✓ {len(products)} products created")

        # Discount codes
        discounts = [
            Discount(code='WELCOME10', discount_type='percent', value=10, is_active=True, min_order_amount=100),
            Discount(code='ORIAL20', discount_type='percent', value=20, is_active=True, min_order_amount=500, max_uses=50),
            Discount(code='FREE50', discount_type='fixed', value=50, is_active=True, min_order_amount=300),
        ]
        for d in discounts:
            db.session.add(d)
        print("✓ Discount codes created (WELCOME10, ORIAL20, FREE50)")

        # Site settings
        settings_data = {
            'free_shipping_threshold': '200',
            'shipping_cost': '9.95',
            'store_name': 'ORIAL Fine Jewellery',
            'contact_email': 'hello@orial.com',
        }
        for k, v in settings_data.items():
            s = SiteSettings(key=k, value=v)
            db.session.add(s)

        # Navigation items
        navs = [
            NavigationItem(label='Shop', url='shop.products', display_order=1),
            NavigationItem(label='Our Story', url='main.our_story', display_order=2),
            NavigationItem(label='Bespoke', url='main.bespoke', display_order=3),
        ]
        for n in navs:
            db.session.add(n)
        print("✓ Navigation items created")

        db.session.commit()
        print("\n✅ Seed complete!")
        print("   Admin login: admin@orial.com / admin123")
        print("   Test user:   jane@example.com / test123")
        print("   Discount:    WELCOME10 (10% off orders over Rs100)")


if __name__ == '__main__':
    seed()
