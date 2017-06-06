from django.core.exceptions import ObjectDoesNotExist

from karma.models import Wallet, KarmaConfig, LikeTransaction


class WalletMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.wallet = None
        request.like_ids = set()

        if request.cookie_id:
            try:
                request.wallet = Wallet.objects.get(cookie_id=request.cookie_id)
            except ObjectDoesNotExist:
                if request.user.is_staff:
                    staff_balance = KarmaConfig.MODERATOR_WALLET
                    request.wallet = Wallet.objects.create(
                        cookie_id=request.cookie_id,
                        max_balance=staff_balance,
                        current_balance=staff_balance
                    )

            if request.wallet:
                request.like_ids = set(LikeTransaction.objects.filter(from_wallet=request.wallet).values_list('comment_id', flat=True))

        return self.get_response(request)

