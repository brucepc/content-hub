from django.conf.urls import patterns, url
from catalogue import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='manage-index'),
    url(r'^categories/$', views.categories, name='manage-categories'),
    url(r'^categories/add/$', views.add_category, name='add-category'),
    url(r'^categories/edit/$', views.edt_category, name='edit-category'),
    url(r'^categories/delete/$', views.del_category, name='delete-category'),
    url(r'^hiddens/$', views.hiddens, name='manage-hiddens'),
    url(r'^featureds/$', views.featureds, name='manage-featureds'),
    url(r'^tags/$', views.tags, name='manage-tags'),
    url(r'^tags/delete/$', views.del_tag, name='delete-tag'),
    #
    url(r'^groups/$', views.groups, name='manage-groups'),
    #
    url(r'^notification/$', views.notification, name='manage-notification'),
    #
    url(r'^groups/items/$', views.groups_items, name='manage-groups-items'),
    url(r'^groups/items/(?P<id>\d+)/$', views.group_item_list, name='group-item-list'),
    url(r'^groups/items/(?P<gid>\d+)/(?P<iid>\d+)/$', views.remove_item_from_group, name='remove-item-from-group'),
    url(r'^groups/items/multi/(?P<id>\d+)/$', views.remove_multi, name='remove-multi-items'),
    url(r'^groups/add/$', views.add_group, name='add-group'),
    url(r'^groups/edit/$', views.edt_group, name='edit-group'),
    url(r'^groups/delete/$', views.del_group, name='delete-group'),
    #
    url(r'^table/$', views.table, name='manage-table'),
    url(r'^table/feature/$', views.manage_feature, name='manage-feature'),
    url(r'^table/multifeature/$', views.manage_multifeature, name='manage-multifeature'),
    url(r'^table/multihide/$', views.manage_multihide, name='manage-multihide'),
    url(r'^table/hidden/$', views.manage_hiddens, name='manage-hidden'),
    url(r'^table/multidelete/$', views.manage_multidelete, name='manage-multidelete'),
    url(r'^table/delete/$', views.manage_delete, name='manage-delete'),
    url(r'^table/multigroup/$', views.manage_multigroup, name='manage-multigroup'),
    url(r'^table/multigroup-delete/$', views.manage_delete_multigroup, name='manage-delete-multigroup'),
    url(r'^table/get-item/$', views.get_item, name='get-item'),
    url(r'^table/get-group-items/$', views.get_group_items, name='get-group-items'),
    url(r'^table/update-item/$', views.update_item, name='update-item'),

    url(r'^items/batch/delete/$', views.batch_delete_items, name='batch-delete-items'),

    url(r'^items/edit/$', views.items_edit, name='items-edit'),

    url(r'^d_groups/list/$', views.groups_list, name='groups-list'),
    url(r'^d_groups/create/$', views.groups_create, name='groups-create'),
    url(r'^d_groups/edit/$', views.groups_edit, name='groups-edit'),
    url(r'^d_groups/feature/$', views.groups_feature, name='groups-feature'),
    url(r'^d_groups/delete/$', views.groups_delete, name='groups-delete'),
    url(r'^d_groups/add/$', views.groups_add, name='groups-add'),
    url(r'^d_groups/remove/$', views.groups_remove, name='groups-remove'),
    url(r'^d_groups/batch/delete/$', views.groups_batch_delete, name='groups-batch-delete'),
    url(r'^d_groups/batch/add/$', views.groups_batch_add, name='groups-batch-add'),
    url(r'^d_groups/batch/remove/$', views.groups_batch_remove, name='groups-batch-remove'),

    url(r'^d_tags/edit/$', views.tags_edit, name='tags-edit'),
    url(r'^d_tags/delete/$', views.tags_delete, name='tags-delete'),

    url(r'^d_categories/edit/$', views.categories_edit, name='categories-edit'),
    url(r'^d_categories/delete/$', views.categories_delete, name='categories-delete'),

)