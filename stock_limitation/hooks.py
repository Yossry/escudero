# -*- coding: utf-8 -*-


def pre_init_hook(cr):
    """Loaded before installing the module.

    None of this module's DB modifications will be available yet.

    If you plan to raise an exception to abort install, put all code inside a
    ``with cr.savepoint():`` block to avoid broken databases.

    :param odoo.sql_db.Cursor cr:
        Database cursor.
    """
    pass



def post_init_hook(cr, registry):
    """Loaded after installing the module.

    This module's DB modifications will be available.

    :param odoo.sql_db.Cursor cr:
        Database cursor.

    :param odoo.modules.registry.RegistryManager registry:
        Database registry, using v7 api.
    """
    pass


def uninstall_hook(cr, registry):
    """Loaded before uninstalling the module.

    This module's DB modifications will still be available. Raise an exception
    to abort uninstallation.

    :param odoo.sql_db.Cursor cr:
        Database cursor.

    :param odoo.modules.registry.RegistryManager registry:
        Database registry, using v7 api.

    To-do:
     * update stock if this module is uninstalled
    """
    pass


def post_load():
    """Loaded before any model or data has been initialized.

    This is ok as the post-load hook is for server-wide
    (instead of registry-specific) functionalities.
    """
    pass
