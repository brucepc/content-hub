import json
import logging

from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from django.db.models.signals import m2m_changed, pre_delete
from django.http import HttpResponseRedirect, HttpResponse, StreamingHttpResponse
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.template.defaultfilters import slugify
from django.views.decorators.cache import never_cache

from catalogue.forms import AddCategory, EditCategory, DeleteCategory, AddGroup, EditGroup, DeleteGroup, AddContentItemToGroup, DeleteTag
from contentimport.forms import UploadForm, UpdateForm
from contentimport.importer import Importer
from contentimport.lib import generate_tag_scores, category_dictionary
from contentimport.models import ContentItem, Category, Tag, TeacherGroupMembership, TeacherGroup, Package, PackageMembership, Log, SiteSetting

logger = logging.getLogger(__name__)


class JsonResponse(HttpResponse):
    def __init__(self, content={}, mimetype=None, status=None,
             content_type='application/json'):
        super(JsonResponse, self).__init__(json.dumps(content), mimetype=mimetype,status=status, content_type=content_type)
        
@login_required
def index(request):
    if request.method == 'POST':
        add_item_to_group_form = AddContentItemToGroup(request.POST)
        #if add_item_to_group_form.is_valid():
        desired_group = request.POST['title']
        contentitem_ids = request.POST.getlist('members')
        for item in contentitem_ids:
            logging.info(item)
            item_instance = ContentItem.objects.get(pk=item)
            # add to group
            group_instance = TeacherGroup.objects.get(pk=desired_group)
            try:
                (membership, created) = TeacherGroupMembership.objects.get_or_create(item=item_instance, group=group_instance)
                membership.save()
            except:
                pass #fine if it already exists

        return HttpResponseRedirect('/manage/')
    else:
        add_item_to_group_form = AddContentItemToGroup()
        group_list = []
        groups = TeacherGroup.objects.all()
        for group in groups:
            g = {
                'title': group.title,
                'members': [],
            }
            group_members = ContentItem.objects.filter(teachergroup=group)
            for member in group_members:
                g['members'].append(member.title)
            
            group_list.append(g)
        
        noti = SiteSetting.objects.get(name="notifications")
        noti_form = noti.value

        if noti_form == 'True':
            n = Log.objects.all()
        else:
            n = False
    return render(request, 'catalogue/index.html', {"add_item_to_group_form": add_item_to_group_form, "group_list": group_list, 'noti': n, 'noti_form': noti_form})

@login_required
def notification(request):
    if request.method == 'POST':
        NOTIFY= request.POST.get('notify', False)
        logging.info("NOTIFY: " + str(NOTIFY))
        n = SiteSetting.objects.get(name="notifications")
        if NOTIFY:
            n.value = 'True'
            n.save()
        else:
            n.value = 'False'
            n.save()
    return HttpResponseRedirect('/manage/')

# Tags

@login_required
def tags(request):
    """
    deleting a tag view
    """
    tags = Tag.objects.annotate(uses=Count('contentitem')).order_by('text')
    del_tag_form = DeleteTag()

    return render(request, 'catalogue/tags.html', {
        'del_tag_form': del_tag_form,
        'tags': tags,
    })

@login_required
def del_tag(request):
    """
    user has submitted from the delete category form
    """
    if request.method == 'POST':
        form = DeleteTag(request.POST)
        if form.is_valid():
            category = Tag.objects.get(pk=request.POST['tag_text'])
            category.delete()
    return HttpResponseRedirect('/manage/tags/')
# Item Catalogue
@login_required
def hiddens (request):
    if request.method == 'POST':
        #get list of chosen item to be marked as hidden
        itemToHideIds = request.POST.getlist('item')
        for id in itemToHideIds:
            itemToHide = ContentItem.objects.get(pk=id)
            itemToHide.hidden = True
            itemToHide.save()
        return HttpResponseRedirect('/manage/hiddens/')
    else:
        #get all the items that marked as hidden
        hiddenItems = ContentItem.objects.filter(hidden=True)
        unhiddenItems = ContentItem.objects.exclude(hidden=True)

        return render(request, 'catalogue/hidden.html', { 
            'hiddenItems': hiddenItems,
            'unhiddenItems': unhiddenItems, 
        })
@login_required
def featureds (request):
    if request.method == 'POST':
        #get list of chosen item to be marked as featured
        itemToFeatureIds = request.POST.getlist('item')
        for id in itemToFeatureIds:
            itemToFeature = ContentItem.objects.get(pk=id)
            itemToFeature.featured = True
            itemToFeature.save()
        return HttpResponseRedirect('/manage/featureds/')
    else:
        #get all the items that marked as featured
        featuredItems = ContentItem.objects.filter(featured=True)
        unfeaturedItems = ContentItem.objects.exclude(featured=True)

        return render(request, 'catalogue/featured.html', { 
            'featuredItems': featuredItems,
            'unfeaturedItems': unfeaturedItems, 
        })

# Categories

@login_required
def categories(request):
    """
    view for managing categories
    """
    add_category_form = AddCategory()
    edt_category_form = EditCategory()
    del_category_form = DeleteCategory()

    cat_dict = category_dictionary()

    return render(request, 'catalogue/categories.html', {
        'add_category_form': add_category_form,
        'categories': cat_dict,
    })

@login_required
def add_category(request):
    """
    user has submitted from the add category form
    """
    if request.method == 'POST':
        form = AddCategory(request.POST)
        if form.is_valid():
            new_category = form.save(commit=False)

            #check the depth of the new category
            depth = 0
            the_id = new_category.parent_id
            while True:
                if the_id is None or depth >= 3:
                    break
                else:
                    depth = depth+1
                    the_id = Category.objects.get(pk=the_id).parent_id
            logger.info('New category depth: ' + str(depth))

            new_category.name = new_category.name
            if not new_category.name.isspace():
                if depth < 3:
                    new_category.save()
                else:
                    return HttpResponseRedirect('/manage/categories/?deptherror=True')
        else:
            return HttpResponseRedirect('/manage/categories/?nameerror=True')

    return HttpResponseRedirect('/manage/categories/')

@login_required
def edt_category(request):
    """
    user has submitted from the edit category form
    """
    if request.method == 'POST':
        form = EditCategory(request.POST)
        if form.is_valid():
            new_name = request.POST['new_name']
            category = Category.objects.get(pk=request.POST['name'])
            category.name = new_name
            if not category.name.isspace():
                category.save()
    return HttpResponseRedirect('/manage/categories/')

@login_required
def del_category(request):
    """
    user has submitted from the delete category form
    """
    if request.method == 'POST':
        form = DeleteCategory(request.POST)
        if form.is_valid():
            category = Category.objects.get(pk=request.POST['name'])
            if category.locked:
                pass
            else:
                category.delete()
    return HttpResponseRedirect('/manage/categories/')


# Groups

@login_required
def groups(request):
    """
    view for managing groups
    """
    add_group_form = AddGroup()
    edt_group_form = EditGroup()
    del_group_form = DeleteGroup()

    return render(request, 'catalogue/groups.html', {
        'add_group_form': add_group_form,
        'edt_group_form': edt_group_form,
        'del_group_form': del_group_form,
    })

@login_required
def add_group(request):
    """
    user has submitted from the add group form
    """
    if request.method == 'POST':
        form = AddGroup(request.POST)
        if form.is_valid():
            new_group = form.save(commit=False)
            new_group.title = new_group.title
            if not new_group.title.isspace():
                new_group.save()
    return HttpResponseRedirect('/manage/groups/')

@login_required
def edt_group(request):
    """
    user has submitted from the edit group form
    """
    if request.method == 'POST':
        form = EditGroup(request.POST)
        if form.is_valid():
            new_name = request.POST['new_name']
            group = TeacherGroup.objects.get(pk=request.POST['title'])
            group.title = new_name
            if not group.title.isspace():
                group.save()
    return HttpResponseRedirect('/manage/groups/')

@login_required
def del_group(request):
    """
    user has submitted from the delete group form
    """
    if request.method == 'POST':
        form = DeleteGroup(request.POST)
        if form.is_valid():
            group = TeacherGroup.objects.get(pk=request.POST['title'])
            group.delete()
    return HttpResponseRedirect('/manage/groups/')

@login_required
def groups_items(request):
    groups = TeacherGroup.objects.all()
    return render(request, 'catalogue/groups-items.html', {
        "groups": groups,
    })
@login_required
def group_item_list(request, id):
    group_items_list = TeacherGroup.objects.get(pk=id).members.all()
    group_name = TeacherGroup.objects.get(pk=id)
    return render(request, 'catalogue/group-items-list.html', {
        "groupId": id,
        "items": group_items_list,
        "groupName": group_name,
    })

@login_required
def remove_item_from_group(request, gid, iid):
    itemToRemove = ContentItem.objects.get(pk = iid)
    groupToRemoveItemFrom = TeacherGroup.objects.get(pk = gid)
    item = TeacherGroupMembership.objects.get(group= groupToRemoveItemFrom, item= itemToRemove)
    item.delete()
    return HttpResponseRedirect('/manage/groups/items/'+gid)

@login_required
def remove_multi (request, id):
    if request.method == 'POST':
        #get list of chosen item to be marked as hidden
        itemToRemoveIds = request.POST.getlist('item')
        for iid in itemToRemoveIds:
            itemToRemove = ContentItem.objects.get(pk = iid)
            groupToRemoveItemFrom = TeacherGroup.objects.get(pk = id)
            item = TeacherGroupMembership.objects.get(group= groupToRemoveItemFrom, item= itemToRemove)
            item.delete()
    return HttpResponseRedirect('/manage/groups/items/'+id)


"""
functionality of manage table is done using ajax ... after making the action you must refresh the page to see the effect
TODO still need to update the page content using ajax 'without refreshing the page' after each event
"""
@login_required
def table(request):
    objects = ContentItem.objects.all()
    groups = TeacherGroup.objects.all()
    updateForm = UploadForm()
    # print objects
    return render(request, 'catalogue/manage-table.html', {'objects': objects, 'groups': groups, 'updateForm': updateForm})

def get_item(request):
    pk = request.POST['id']
    c = ContentItem.objects.get(pk=pk)
    upf = UploadForm(instance=c)
    myform = {'form':{ 
        'title': str(upf['title']),
        'description': str(upf['description']),
        'categories': str(upf['categories']),
        'content_file': str(upf['content_file']),
        'tags': str(upf['tags']),
        'id': c.id,
        },
    }
    return JsonResponse(myform)

@login_required
def manage_hiddens(request):
    exit_state = False
    if request.POST:
        if request.is_ajax():
            i = ContentItem.objects.get(pk=request.POST['id'])
            if i.hidden:
                i.hidden = False
                exit_state = False
                try:
                    i.save(dont_index=True)
                except Exception as e:
                    print(e)
            else:
                i.hidden = True
                exit_state = True
                try:
                    i.save(dont_index=True)
                except Exception as e:
                    print(e)
        resp_data = {'result': exit_state,}
        return JsonResponse(resp_data)

#feature-unfeature item
@login_required
def manage_feature(request):
    exit_state = False
    if request.POST:
        if request.is_ajax():

            fcount = ContentItem.objects.filter(featured='1').count()
            maxfeatured = False

            i = ContentItem.objects.get(pk=request.POST['id'])
            if i.featured:
                fcount = fcount -1
                i.featured = False
                exit_state = False
                try:
                    i.save(dont_index=True)
                except Exception as e:
                    print(e)
            else:
                if fcount >= 10:
                    exit_state = False
                    maxfeatured = True
                else:
                    i.featured = True
                    exit_state = True
                    try:
                        i.save(dont_index=True)
                    except Exception as e:
                        print(e)

        resp_data = {'result': exit_state, 'maxfeatured': maxfeatured,}
        return JsonResponse(resp_data)

@login_required
def manage_multifeature(request):
    if request.POST:
        if request.is_ajax():
            ids = request.POST.getlist('ids')
            for id in ids:
                i = ContentItem.objects.get(pk=id)
                if i.featured:
                    i.featured = False
                    try:
                        i.save(dont_index=True)
                    except Exception as e:
                        print(e)
                else:
                    i.featured = True
                    try:
                        i.save(dont_index=True)
                    except Exception as e:
                        print(e)

@login_required
def manage_multihide(request):
    if request.POST:
        if request.is_ajax():
            ids = request.POST.getlist('ids')
            for id in ids:
                i = ContentItem.objects.get(pk=id)
                if i.hidden:
                    i.hidden = False
                    try:
                        i.save(dont_index=True)
                    except Exception as e:
                        print(e)
                else:
                    i.hidden = True
                    try:
                        i.save(dont_index=True)
                    except Exception as e:
                        print(e)

@login_required
def manage_delete(request):
    if request.POST:
        if request.is_ajax():
            try:
                c = ContentItem.objects.get(pk=request.POST['id'])
                c.categories.clear()
                c.delete()
                resp_data = {'result': True,}
            except:
                resp_data = {'result': False,}
        return JsonResponse(resp_data)

#not used?
@login_required
def manage_multidelete(request):
    if request.POST:
        if request.is_ajax():
            ids = request.POST.getlist('ids')
            for id in ids:
                c = ContentItem.objects.get(pk=id)
                c.categories.clear()
                c.delete()

@login_required
def manage_multigroup(request):
    if request.POST:
        if request.is_ajax():
            ids = request.POST.getlist('ids')
            group = request.POST['group']
            for id in ids:
                itemToGroup = ContentItem.objects.get(pk=id)
                groupToUse = TeacherGroup.objects.get(pk = group)
                item = TeacherGroupMembership(group= groupToUse, item= itemToGroup)
                item.save()

@login_required
def manage_delete_multigroup(request):
    if request.POST:
        if request.is_ajax():
            ids = request.POST.getlist('ids')
            group = request.POST['group']
            for id in ids:
                itemToGroup = ContentItem.objects.get(pk=id)
                groupToUse = TeacherGroup.objects.get(pk = group)
                item = TeacherGroupMembership.objects.get(group= groupToUse, item= itemToGroup)
                item.delete()
                print(groupToUse.members.all())
def update_item(request):
    if request.POST:
        if request.is_ajax():
            instance = ContentItem.objects.get(pk=request.POST['id'])
            # form = UploadForm(data=request.POST, instance=instance)
            tags = request.POST.getlist('tags[]')
            categories = request.POST.getlist('categories[]')
            title = request.POST['title']
            description = request.POST['description']
            tags_list = []
            categories_list = []
            for tag in tags:
                t = Tag.objects.get(pk=tag)
                tags_list.append(t)
            for category in categories:
                ca = Category.objects.get(pk=category)
                categories_list.append(ca)
            instance.title = title
            instance.description = description
            instance.tags = tags_list
            instance.categories = categories_list
            instance.save()
        objects1 = ContentItem.objects.all()
        try:
            return JsonResponse({'name':'objects1'})
        except Exception as e:
            print(e)
@login_required
def get_group_items(request):
    if request.POST:
        if request.is_ajax():
            item_list = []
            group = TeacherGroup.objects.get(pk=request.POST['group_id'])
            items = group.members.all()
            for item in items:
                item_list.append(item.pk)
    return JsonResponse({'items': item_list})

# class AjaxableResponseMixin(object):
#     def render_to_json_response(self, context, **response_kwargs):
#         data = json.dumps(context)
#         response_kwargs['content_type'] = 'application/json'
#         return HttpResponse(data, **response_kwargs)

#     def form_invalid(self, form):
#         response = super(AjaxableResponseMixin, self).form_invalid(form)
#         if self.request.is_ajax():
#             return self.render_to_json_response(form.errors, status=400)
#         else:
#             return response

#     def form_valid(self, form):
#         response = super(AjaxableResponseMixin, self).form_valid(form)
#         if self.request.is_ajax():
#             data = {
#                 'pk': self.object.pk,
#             }
#             return self.render_to_json_response(data)
#         else:
#             return response

# class ContentItemModal(AjaxableResponseMixin, UpdateView):
#     template_name = 'catalo/edit.html'
#     form_class = UploadForm
#     model = ContentItem
#     # success_url = '/'
#     def get_object(self, query_set=None):
#         obj = ContentItem.objects.get(id=1)
#         return obj

@login_required
def batch_delete_items(request):
    """
    delete requested items from array in POST request
    """
    response = { 'result': False }

    if request.POST:
        if request.is_ajax():
            item_list = request.POST.getlist('ids[]') # not sure why the name changes to add [] to the end...
            try:
                #ContentItem.objects.filter(pk__in=item_list).exclude(uploaded=False).delete()
                for id in item_list:
                    c = ContentItem.objects.get(pk=id)
                    c.categories.clear()
                    c.delete()
                response = { 'result': True }
            except:
                pass

    return JsonResponse(response)
    
#
#   ITEMS
#
def items_edit(request, template='browse/edit.html'):
    """
    supply a form to edit a content item, preloaded with details
    """
    tags_list = list(Tag.objects.values_list('text', flat=True))
    tags_json = json.dumps(tags_list)

    if request.method == 'POST':

        form = UpdateForm(request.POST)

        if form.is_valid():
            i = Importer()
            itemid = request.POST['id']
            item = ContentItem.objects.exclude(uploaded=False).get(pk=itemid)

            item.title = request.POST['title']
            item.description = request.POST['description']

            category = request.POST['c']

            cat_to_ci_map = []
            if category is not None:
                CategoryThroughModel = ContentItem.categories.through
                CategoryThroughModel.objects.filter(contentitem=item).delete()

                # i.e. leave with no categories if c is 0
                if category != '0':
                    cat_to_ci_map.append([ item.pk, [ category ] ])
                    i.create_category_relationships(cat_to_ci_map, id_list=True)

            tags = request.POST['tags'].split(',')


            tag_to_ci_map = []
            if tags is not None:
                TagThroughModel = ContentItem.tags.through
                TagThroughModel.objects.filter(contentitem=item).delete()
                tag_to_ci_map.append([ item.id, tags ])
                i.create_tags(tags)
                i.create_tag_relationships(tag_to_ci_map, id_list=False)

            #i.force_update_of_index()

            logger.info("Updating tag scores")
            generate_tag_scores()

            item.save()

            return JsonResponse({'result': True, 'id': itemid, 'title': item.title})
        else:
            return JsonResponse({'result': False})

    else:
        item = ContentItem.objects.exclude(uploaded=False).get(pk=request.GET['id'])
        form = UpdateForm(instance=item)

        existing_tags = []
        for tag in item.tags.all():
            existing_tags.append(tag.text)

        existing_tags_string = ','.join(existing_tags)

        existing_categories = []
        for cat in item.categories.all():
            existing_categories.append(cat.pk)

        if len(existing_categories) > 0:
            existing_categories = existing_categories[-1]

        context = {
            'form': form,
            'item_id': item.pk,
            'tags_json': tags_json,
            'categories': category_dictionary(),
            'existing_tags': existing_tags_string,
            'existing_category': existing_categories, # should only be one
        }

        return render_to_response(template, context, context_instance=RequestContext(request))


#
#   GROUPS
#
@never_cache
def groups_list(request):
    MEMBER_LENGTH = 10
    if request.GET and request.is_ajax():
        try:
            group = TeacherGroup.objects.get(pk=request.GET['id'])
            members = list(ContentItem.objects.filter(teachergroup__pk=group.pk).values_list('title', flat=True).order_by('-id')[:MEMBER_LENGTH])
            member_length = ContentItem.objects.filter(teachergroup__pk=group.pk).count()

            if member_length > MEMBER_LENGTH:
                length_diff = (member_length - MEMBER_LENGTH) + 1
                del members[-1]
                members.append('(and ' + str(length_diff) + ' more...)')

            return JsonResponse({'id': group.pk, 'title': group.title, 'members': members })
        except:
            return
    else:
        groups = TeacherGroup.objects.values_list('title', flat=True).order_by('id')
        return JsonResponse({'groups': list(groups)})

@login_required
def groups_create(request):
    resp = {'result': False}

    if request.POST:
        if request.is_ajax():
            group_name = request.POST['group_name'].strip()
            if not group_name.isspace():
                try:
                    existingCount = TeacherGroup.objects.filter(title__iexact=group_name).count()
                    if(existingCount <= 0):
                        group, created = TeacherGroup.objects.get_or_create(title=group_name)
                        if created:
                            resp = {'result': True, 'id': group.pk, 'created': created}
                            group.save()
                except e:
                    pass

    return JsonResponse(resp)

@login_required
def groups_edit(request):
    resp = {'result': False}

    if request.POST:
        if request.is_ajax():
            new_title = request.POST['new_title'].strip()
            if not new_title.isspace():
                try:
                    existingCount = TeacherGroup.objects.filter(title__iexact=new_title).count()
                    if(existingCount <= 0):
                        group = TeacherGroup.objects.get(pk=request.POST['id'])
                        group.title = new_title
                        if not group.title.isspace():
                            group.save()
                        resp = {'result': True}
                except:
                    pass

    return JsonResponse(resp)

@login_required
def groups_feature(request):
    resp = {'result': False}

    if request.POST:
        if request.is_ajax():
            try:
                fcount = TeacherGroup.objects.filter(featured='1').count()
                maxfeatured = False

                group = TeacherGroup.objects.get(pk=request.POST['id'])
                if group.featured:
                    fcount = fcount -1
                    group.featured = False
                else:
                    if fcount >= 10:
                        group.featured = False
                        maxfeatured = True
                    else:
                        group.featured = True
                group.save()

                resp = {'result': group.featured, 'maxfeatured': maxfeatured,}
            except:
                pass

    return JsonResponse(resp)

@login_required
def groups_delete(request):
    """
    delete the requested lesson (group)
    """
    response = { 'result': False }

    if request.POST and request.is_ajax():
        try:
            TeacherGroup.objects.get(pk=request.POST['id']).delete()
            response = { 'result': True }
        except:
            pass

    return JsonResponse(response)

@login_required
def groups_add(request):
    if request.POST:
        if request.is_ajax():
            try:
                id = request.POST['id']
                group = request.POST['group']
                itemToGroup = ContentItem.objects.get(pk=id)
                groupToUse = TeacherGroup.objects.get(pk=group)
                item = TeacherGroupMembership(group=groupToUse, item=itemToGroup)
                item.save()
                resp = {'result': True}
            except:
                resp = {'result': False}

        return JsonResponse(resp)

@login_required
def groups_remove(request):
    if request.POST:
        if request.is_ajax():
            try:
                id = request.POST['id']
                group = request.POST['group']
                itemToGroup = ContentItem.objects.get(pk=id)
                groupToUse = TeacherGroup.objects.get(pk=group)
                item = TeacherGroupMembership.objects.get(group=groupToUse, item=itemToGroup).delete()
                resp = {'result': True}
            except:
                resp = {'result': False}

        return JsonResponse(resp)

@login_required
def groups_batch_delete(request):
    """
    delete the requested lessons (groups)
    """
    response = { 'result': False }

    if request.POST and request.is_ajax():
        try:
            TeacherGroup.objects.filter(pk__in=request.POST.getlist('ids[]')).delete()
            response = { 'result': True }
        except:
            pass

    return JsonResponse(response)

@login_required
def groups_batch_add(request):
    """
    add requested items from array in POST request to requested group
    """
    response = { 'result': False }
    create_list = []

    if request.POST and request.is_ajax():
        try:
            item_list = request.POST.getlist('ids[]')
            group = TeacherGroup.objects.get(pk=request.POST['group'])
            items = ContentItem.objects.filter(pk__in=item_list)
            for item in items:
                create_list.append(TeacherGroupMembership(item=item, group=group))
            TeacherGroupMembership.objects.bulk_create(create_list)
            response = { 'result': True }
        except:
            pass

    return JsonResponse(response)

@login_required
def groups_batch_remove(request):
    """
    remove requested items from array in POST from requested group
    """
    response = { 'result': False }

    if request.POST and request.is_ajax():
        try:
            item_list = request.POST.getlist('ids[]')
            group = TeacherGroup.objects.get(pk=request.POST['group'])
            items = ContentItem.objects.filter(pk__in=item_list)
            for item in items:
                TeacherGroupMembership.objects.get(item=item, group=group).delete()
            response = { 'result': True }
        except Exception as e:
            logger.exception(e)

    return JsonResponse(response)


#
# TAGS
#
@login_required
def tags_edit(request):
    response = { 'result': False }

    if request.POST and request.is_ajax():
        try:
            new_text = request.POST['new_text']

            if new_text:
                if not new_text.isspace():
                    tag_id = request.POST['id']
                    tag = Tag.objects.filter(locked=False).get(pk=tag_id)
                    tag.text = new_text
                    tag.save()

                    response = { 'result': True }
        except:
            response = { 'result': False, 'reason': 'Exception' }

    return JsonResponse(response)

@login_required
def tags_delete(request):
    response = { 'result': False }
    if request.POST and request.is_ajax():
        try:
            TagThroughModel = ContentItem.tags.through
            tag_id = request.POST['id']
            tag = Tag.objects.filter(locked=False).get(pk=tag_id)
            TagThroughModel.objects.filter(tag=tag).delete()
            tag.delete()
            response = { 'result': True }
        except:
            response = { 'result': False, 'reason': 'Exception' }

    return JsonResponse(response)

#
# CATEGORIES
#
@login_required
def categories_edit(request):
    response = { 'result': False }

    if request.POST and request.is_ajax():
        try:
            new_name = request.POST['new_name']

            if new_name:
                if not new_name.isspace():
                    category_id = request.POST['id']
                    category = Category.objects.filter(locked=False).get(pk=category_id)
                    category.name = new_name
                    category.save()

                    response = { 'result': True }
        except:
            response = { 'result': False, 'reason': 'Exception' }

    return JsonResponse(response)

@login_required
def categories_delete(request):
    response = { 'result': False }
    if request.POST and request.is_ajax():
        try:
            CategoryThroughModel = ContentItem.categories.through
            category_id = request.POST['id']

            category = Category.objects.filter(locked=False).get(pk=category_id)
            subcategories = Category.objects.filter(locked=False).filter(parent=category)
            subsubcategories = Category.objects.filter(locked=False).filter(parent__in=subcategories)

            CategoryThroughModel.objects.filter(category=category).delete()
            CategoryThroughModel.objects.filter(category__in=subcategories).delete()
            CategoryThroughModel.objects.filter(category__in=subsubcategories).delete()

            category.delete()
            subcategories.delete()
            subsubcategories.delete()

            response = { 'result': True }
        except:
            response = { 'result': False, 'reason': 'Exception' }

    return JsonResponse(response)