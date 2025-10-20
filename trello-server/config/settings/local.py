from .common import Common


class Local(Common):
  DEBUG = True

  # Testing
  INSTALLED_APPS = Common.INSTALLED_APPS

  # Mail