from django.contrib import admin
from accounts.models import PersonAccount, Live, ShopifyAccess, OTP

class PersonAccountAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone', 'address', 'id_options', 'id_image', 'account_type', 'user_id')

    def custom_display(self, obj):
        # Define your custom display logic here
        if obj.first_name or obj.last_name or obj.phone or obj.address or obj.id_options or obj.id_image or obj.account_type or obj.user_id:
            return obj.first_name + " " + obj.last_name + " - " + obj.account_type
        else:
            return "Admin account. Kindly refer to Users under authentication and authorization tab."

    custom_display.short_description = 'Custom Display'

admin.site.register(PersonAccount, PersonAccountAdmin)
admin.site.register(Live)
admin.site.register(ShopifyAccess)
admin.site.register(OTP)