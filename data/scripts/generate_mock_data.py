import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

from faker import Faker

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import create_app
from app.extensions import db
from app.models import (
    AdPerformance,
    CouponUsage,
    MarketingCampaign,
    Order,
    Product,
    Review,
    User,
    UserBehavior,
)

fake = Faker("zh_CN")


def random_dt_within(days=90):
    return datetime.utcnow() - timedelta(days=random.randint(0, days), hours=random.randint(0, 23))


def seed_data():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        regions = ["华北", "华东", "华南", "华中", "西南", "东北"]
        categories = ["服装", "家电", "美妆", "数码", "家居", "母婴"]
        coupon_types = ["满200减50", "8折券", "新人券", None]
        review_tags = ["质量差", "物流慢", "包装破损", "性价比高", "尺码不准"]

        users = []
        for i in range(500):
            user = User(
                username=f"user_{i + 1}",
                age=random.randint(18, 55),
                gender=random.choice(["male", "female"]),
                region=random.choice(regions),
                created_at=random_dt_within(300),
                last_login_at=random_dt_within(7),
            )
            users.append(user)
        db.session.add_all(users)
        db.session.flush()

        products = []
        for i in range(120):
            price = round(random.uniform(30, 1200), 2)
            cost = round(price * random.uniform(0.4, 0.8), 2)
            products.append(
                Product(
                    name=f"{random.choice(categories)}商品{i + 1}",
                    category=random.choice(categories),
                    price=price,
                    cost=cost,
                    stock=random.randint(0, 800),
                    rating=round(random.uniform(2.5, 5.0), 1),
                    created_at=random_dt_within(365),
                )
            )
        db.session.add_all(products)
        db.session.flush()

        campaigns = []
        for i in range(10):
            start = datetime.utcnow() - timedelta(days=random.randint(10, 70))
            end = start + timedelta(days=random.randint(7, 30))
            campaigns.append(
                MarketingCampaign(
                    name=f"活动{i + 1}",
                    campaign_type=random.choice(["满减", "折扣", "直播", "广告"]),
                    cost=round(random.uniform(2000, 30000), 2),
                    start_time=start,
                    end_time=end,
                )
            )
        db.session.add_all(campaigns)
        db.session.flush()

        orders = []
        for i in range(6000):
            user = random.choice(users)
            product = random.choice(products)
            campaign = random.choice(campaigns + [None])
            qty = random.randint(1, 5)
            amount = round(product.price * qty * random.uniform(0.8, 1.0), 2)
            pay_status = random.choices(["paid", "pending"], weights=[0.9, 0.1])[0]
            refund_status = random.choices(["none", "partial", "full"], weights=[0.86, 0.1, 0.04])[0]
            orders.append(
                Order(
                    order_no=f"ORD{datetime.utcnow().strftime('%Y%m%d')}{i:06d}",
                    user_id=user.id,
                    product_id=product.id,
                    campaign_id=campaign.id if campaign else None,
                    coupon_type=random.choice(coupon_types),
                    quantity=qty,
                    amount=amount,
                    payment_status=pay_status,
                    refund_status=refund_status,
                    created_at=random_dt_within(120),
                )
            )
        db.session.add_all(orders)

        behaviors = []
        for _ in range(20000):
            behaviors.append(
                UserBehavior(
                    user_id=random.choice(users).id,
                    product_id=random.choice(products).id,
                    behavior_type=random.choices(
                        ["view", "add_to_cart", "favorite", "login"],
                        weights=[0.7, 0.15, 0.1, 0.05],
                    )[0],
                    created_at=random_dt_within(60),
                )
            )
        db.session.add_all(behaviors)

        reviews = []
        for _ in range(2500):
            score = random.randint(1, 5)
            tags = ",".join(random.sample(review_tags, k=random.randint(1, 2)))
            reviews.append(
                Review(
                    user_id=random.choice(users).id,
                    product_id=random.choice(products).id,
                    score=score,
                    tags=tags,
                    content=fake.sentence(nb_words=12),
                    created_at=random_dt_within(120),
                )
            )
        db.session.add_all(reviews)

        coupon_usages = []
        for _ in range(3000):
            before = round(random.uniform(60, 900), 2)
            discount = round(random.uniform(5, 120), 2)
            used = random.random() < 0.7
            after = max(round(before - discount, 2), 0)
            campaign = random.choice(campaigns)
            coupon_usages.append(
                CouponUsage(
                    user_id=random.choice(users).id,
                    campaign_id=campaign.id,
                    coupon_type=random.choice(["满200减50", "8折券", "新人券"]),
                    discount_amount=discount,
                    used=used,
                    amount_before=before,
                    amount_after=after if used else before,
                    created_at=random_dt_within(90),
                )
            )
        db.session.add_all(coupon_usages)

        ad_stats = []
        for campaign in campaigns:
            for offset in range(30):
                day = (datetime.utcnow() - timedelta(days=offset)).date()
                clicks = random.randint(100, 2000)
                conversions = random.randint(20, 300)
                cost = round(random.uniform(100, 1500), 2)
                gmv = round(random.uniform(2000, 30000), 2)
                ad_stats.append(
                    AdPerformance(
                        campaign_id=campaign.id,
                        stat_date=day,
                        clicks=clicks,
                        conversions=conversions,
                        cost=cost,
                        gmv=gmv,
                    )
                )
        db.session.add_all(ad_stats)
        db.session.commit()
        print("Mock data generated successfully.")


if __name__ == "__main__":
    seed_data()