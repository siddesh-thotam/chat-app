from .models import ChatGroup

def user_groupchats(request):
    if request.user.is_authenticated:
        groups = ChatGroup.objects.filter(members=request.user)
        group_list = []
        for group in groups:
            # For group chats, use groupchat_name if available
            if group.groupchat_name:
                display_name = group.groupchat_name
            else:
                # For private chats, show the other user's name
                other_members = group.members.exclude(pk=request.user.pk)
                if other_members.exists():
                    other = other_members.first()
                    display_name = getattr(other.profile, 'name', other.username)
                else:
                    display_name = group.group_name
            group_list.append({
                'group_name': group.group_name,
                'display_name': display_name
            })
        return {'user_groupchats': group_list}
    return {'user_groupchats': []}
