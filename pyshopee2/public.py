from .base import BaseModule


class Public(BaseModule):
    def get_shop_by_partner(self, **kwargs):
        """

        :param kwargs
        :return

        """
        return self.client.execute("public/get_shop_by_partner", "GET", kwargs)

    def get_refresh_token_by_upgrade_code(self, **kwargs):
        """

        :param kwargs
        :return

        """
        return self.client.execute("public/get_refresh_token_by_upgrade_code", "POST", kwargs)
