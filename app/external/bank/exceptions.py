class BankApiError(Exception):
    pass


class BankPaymentNotFoundError(BankApiError):
    pass
