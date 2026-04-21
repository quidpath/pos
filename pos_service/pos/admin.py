from django.contrib import admin

# POS Service Admin
# Following Single Source of Truth architecture:
# - Products are managed in Inventory service admin
# - POS admin only manages POS-specific transactional data

# TODO: Register POS-specific models here (POSOrder, POSSession, etc.) when they are created
# For now, this is a placeholder to prevent import errors
