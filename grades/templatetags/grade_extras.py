from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    try:
        # direct lookup
        if dictionary is None:
            return ""
        if key in dictionary:
            return dictionary.get(key, "")
        # try integer conversion
        try:
            ik = int(key)
            if ik in dictionary:
                return dictionary.get(ik, "")
        except Exception:
            pass
        # try string conversion
        sk = str(key)
        return dictionary.get(sk, "")
    except Exception:
        return ""
