from django.shortcuts import render
from django.urls import reverse

def process_overview_dict(overview : dict) -> dict:
    """
    Process the overview dictionary and returns the processed dictionary
    """
    overview["add_url"] = reverse(overview["add_url_name"])
    if overview["element_url_key"] is None:
        overview["element_url_key"] = overview["t_keys"][0]
    overview["table_content"] = []
    overview["first_t_heading"] = overview["t_headings"].pop(0)
    
    # We extract the first field of the normal table because then we can not center the first column in jinja
    for i in range(len(overview["elements"])):
        element = overview["elements"][i]
        row = {}
        row["first_field"] = _get_attr(element, overview["t_keys"][0])
        row_content = []
        for j in range(1, len(overview["t_keys"])):
            key = overview["t_keys"][j]
            row_content.append(_get_attr(element, key))
        row["content"] = row_content
        if overview.get("info_url_name", None) is not None:
            row["info_url"] = reverse(overview["info_url_name"], args=[_get_attr(element, overview["element_url_key"])])
        if overview.get("edit_url_name", None) is not None:
            row["edit_url"] = reverse(overview["edit_url_name"], args=[_get_attr(element, overview["element_url_key"])])
        if overview.get("delete_url_name", None) is not None:
            row["delete_url"] = reverse(overview["delete_url_name"], args=[_get_attr(element, overview["element_url_key"])])
        overview["table_content"].append(row)
   
    return overview
        

def _get_attr(obj, attr):
    value = None
    if hasattr(obj, "__getitem__"):
        value = obj[attr]
    else:
        value = getattr(obj, attr)
    if str(value) == "True":
        value = "✅"
    elif str(value) == "False":
        value = "-"
    elif value is None:
        value = "-"
    return value
        
def message(request, message : str, url_name : str = "", url_args : list = []):
    if url_name == "":
        url_name = "index"
    # Check if url_name can be reversed or its a direct url
    try:
        reverse(url_name, args=url_args)
    except:
        return render(request, "lac/message.html", {"message": message, "url": url_name})
    
    return render(request, "lac/message.html", {"message": message, "url": reverse(url_name, args=url_args)})