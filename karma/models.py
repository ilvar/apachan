from __future__ import unicode_literals

import datetime
import decimal

from django.db import models
from django.db.models import F

from apa.models import Comment, Lenta
from apa.utils import get_tz


class KarmaConfig():
    DEFAULT_WALLET_CAP = 100 * 100
    MODERATOR_WALLET = 1000 * 100

    TYPE_LIKE = "like"
    TYPE_COMMENT = "comment"
    TYPE_CAT = "cat"
    TYPE_CHOICES = (
        (TYPE_LIKE, "Like"),
        (TYPE_COMMENT, "Comment"),
        (TYPE_CAT, "Change category"),
    )

    TYPE_COSTS = {
        TYPE_LIKE: 100,
        TYPE_COMMENT: 30,
        TYPE_CAT: 50
    }

    TAX = 0.1
    LIKE_CAP_INCREASE = 100


class Wallet(models.Model):
    cookie_id = models.CharField(max_length=64, primary_key=True)
    max_balance = models.IntegerField(default=KarmaConfig.DEFAULT_WALLET_CAP)
    current_balance = models.IntegerField(default=0)
    last_add = models.DateTimeField(default=datetime.datetime.now)
    last_sub = models.DateTimeField(default=datetime.datetime.now)

    def get_current_balance(self):
        return decimal.Decimal(self.current_balance) / 100

    def get_current_balance_str(self):
        return '{0:,}'.format(self.current_balance).replace(',', '.')

    def can_like(self):
        return self.current_balance >= LikeTransaction.get_outgoing_cost()
    
    def can_cat(self):
        return self.current_balance >= CatTransaction.get_outgoing_cost()


class GenericTransaction(models.Model):
    to_wallet = models.ForeignKey(Wallet)
    root_id = models.IntegerField()
    comment_id = models.IntegerField()
    canceled = models.BooleanField(default=False)
    dt = models.DateTimeField(auto_now_add=True)

    @classmethod
    def get_incoming_cost(cls):
        return KarmaConfig.TYPE_COSTS[cls.TYPE]

    class Meta:
        abstract = True

    @classmethod
    def cancel(cls, **kwargs):
        transactions = cls.objects.filter(canceled=False, **kwargs)
        transactions.update(canceled=True)
        count = transactions.count()

        to_cost = cls.get_incoming_cost()

        for t in transactions:
            Wallet.objects.filter(pk=t.to_wallet.pk).update(
                current_balance = max(t.to_wallet.current_balance - to_cost, 0),
                last_sub = datetime.datetime.now(get_tz())
            )

        if kwargs.get('comment_id'):
            comment = Comment.objects.get(pk=kwargs.get('comment_id'))
            if comment.root_id and comment.root_id != comment.comment_id:
                 Comment.objects.filter(comment_id=comment.root_id).update(rating=F('rating') - count)


class CatTransaction(GenericTransaction):
    TYPE = KarmaConfig.TYPE_CAT
    
    new_cat = models.IntegerField()

    @classmethod
    def create(cls, from_cookie, comment_id, is_staff, new_cat):
        comment = Comment.objects.get(pk=comment_id)
        from_wallet, _ = Wallet.objects.get_or_create(cookie_id=from_cookie)

        from_cost = cls.get_outgoing_cost()
        if from_wallet.current_balance < from_cost:
            return
    
        if is_staff:
            Wallet.objects.filter(pk=from_wallet.pk).update(
                    current_balance=KarmaConfig.MODERATOR_WALLET
            )
        else:
            Wallet.objects.filter(pk=from_wallet.pk).update(
                    current_balance=F('current_balance') - from_cost,
                    last_sub=datetime.datetime.now(get_tz())
            )
    
        cls.objects.create(
            root_id=comment.root_id or comment.comment_id,
            comment_id=comment_id,
            to_wallet=from_wallet,
            new_cat=new_cat,
            canceled=comment.deleted
        )
    
        if not comment.deleted:
            Lenta.objects.filter(root_id=comment.root_id or comment.comment_id).update(category=new_cat)

    def reapply(self):
        from_cost = self.get_outgoing_cost()
    
        Wallet.objects.filter(pk=self.to_wallet.pk).update(
            current_balance=F('current_balance') - from_cost,
            last_add=datetime.datetime.now(get_tz())
        )
        
        Lenta.objects.filter(root_id=self.root_id).update(category=self.new_cat)
    

class LikeTransaction(GenericTransaction):
    TYPE = KarmaConfig.TYPE_LIKE

    from_wallet = models.ForeignKey(Wallet, related_name='outgoing_transactions')

    class Meta:
        unique_together = (
            ('from_wallet', 'comment_id')
        )

    @classmethod
    def get_outgoing_cost(cls):
        return (1 + KarmaConfig.TAX) * cls.get_incoming_cost()

    @classmethod
    def create(cls, from_cookie, comment_id, is_staff):
        comment = Comment.objects.get(pk=comment_id)
        from_wallet, _ = Wallet.objects.get_or_create(cookie_id=from_cookie)
        to_wallet, _ = Wallet.objects.get_or_create(cookie_id=comment.cookie_id)

        to_cost = cls.get_incoming_cost()
        from_cost = cls.get_outgoing_cost()
        if from_wallet.current_balance < from_cost:
            return

        if is_staff:
            Wallet.objects.filter(pk=from_wallet.pk).update(
                current_balance = KarmaConfig.MODERATOR_WALLET
            )
        else:
            Wallet.objects.filter(pk=from_wallet.pk).update(
                current_balance=F('current_balance') - from_cost,
                max_balance=F('max_balance') + KarmaConfig.LIKE_CAP_INCREASE,
                last_sub = datetime.datetime.now(get_tz())
            )

        cls.objects.create(
            root_id=comment.root_id or comment.comment_id,
            comment_id=comment_id,
            from_wallet=from_wallet,
            to_wallet=to_wallet,
            canceled=comment.deleted
        )

        if not comment.deleted:
            Wallet.objects.filter(pk=to_wallet.pk).update(
                current_balance = min(to_wallet.current_balance + to_cost, to_wallet.max_balance),
                last_add = datetime.datetime.now(get_tz())
            )

            Comment.objects.filter(comment_id=comment.comment_id).update(rating=F('rating') + 1)

    def reapply(self):
        to_cost = self.get_incoming_cost()
        from_cost = self.get_outgoing_cost()

        Wallet.objects.filter(pk=self.from_wallet.pk).update(
            current_balance=F('current_balance') - from_cost,
            max_balance=F('max_balance') + KarmaConfig.LIKE_CAP_INCREASE,
            last_add = datetime.datetime.now(get_tz())
        )

        if not self.canceled:
            Wallet.objects.filter(pk=self.to_wallet.pk).update(
                current_balance=min(self.to_wallet.current_balance + to_cost, self.to_wallet.max_balance),
                last_sub = datetime.datetime.now(get_tz())
            )

            Comment.objects.filter(comment_id=self.comment_id).update(rating=F('rating') + 1)


class CommentTransaction(GenericTransaction):
    TYPE = KarmaConfig.TYPE_COMMENT

    class Meta:
        unique_together = (
            ('root_id', 'comment_id')
        )

    @classmethod
    def create(cls, to_comment_id):
        comment = Comment.objects.get(pk=to_comment_id)

        if not comment.root_id:
            return

        root = Comment.objects.get(pk=comment.root_id)

        if comment.cookie_id == root.cookie_id:
            return

        to_wallet, _ = Wallet.objects.get_or_create(cookie_id=root.cookie_id)

        to_cost = cls.get_incoming_cost()

        cls.objects.create(
            root_id=root.pk,
            comment_id=to_comment_id,
            to_wallet=to_wallet
        )

        Wallet.objects.filter(pk=to_wallet.pk).update(
            current_balance = min(to_wallet.current_balance + to_cost, to_wallet.max_balance),
            last_add = datetime.datetime.now(get_tz())
        )

    def reapply(self):
        to_cost = self.get_incoming_cost()

        if not self.canceled:
            Wallet.objects.filter(pk=self.to_wallet.pk).update(
                current_balance=min(self.to_wallet.current_balance + to_cost, self.to_wallet.max_balance),
                last_sub = datetime.datetime.now(get_tz())
            )



        
