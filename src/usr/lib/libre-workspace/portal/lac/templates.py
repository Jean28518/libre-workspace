from django.shortcuts import render
from django.urls import reverse
from datetime import datetime as DateTime

def process_overview_dict(overview : dict, request=None) -> dict:
    """
    Process the overview dictionary and returns the processed dictionary
    """
    if overview.get("add_url_name", None) is not None:
        overview["add_url"] = reverse(overview["add_url_name"])
    else:
        overview["add_url"] = None
    if "element_url_key" not in overview.keys() or overview["element_url_key"] is None:
        overview["element_url_key"] = overview["t_keys"][0]
    overview["table_content"] = []
    overview["heading_dicts"] = []
    
    
    sort_by = request.GET.get("sort_by", None) if request is not None else None
    sort_order = request.GET.get("sort_order", "asc") if request is not None else "asc"
    for heading in overview["t_headings"]:
        overview_dict = {}
        overview_dict["heading"] = heading
        overview_dict["t_key"] = overview["t_keys"][overview["t_headings"].index(heading)]
        if sort_by == overview_dict["t_key"]:
            overview_dict["is_sorted"] = True
            overview_dict["sort_order"] = sort_order
        else:
            overview_dict["is_sorted"] = False
        
        if request is None:
            overview_dict["sort_url"] = "#"
            overview["heading_dicts"].append(overview_dict)
            continue

        overview_dict["sort_url"] = reverse(request.resolver_match.view_name)
        if sort_by == overview_dict["t_key"] and sort_order == "asc":
            overview_dict["sort_url"] += f"?sort_by={overview_dict['t_key']}&sort_order=desc"
        else:
            overview_dict["sort_url"] += f"?sort_by={overview_dict['t_key']}&sort_order=asc"
        
        # Append all further GET parameters to the sort URL
        for key, value in request.GET.items():
            if key not in ["sort_by", "sort_order"]:
                overview_dict["sort_url"] += f"&{key}={value}"
        
        overview["heading_dicts"].append(overview_dict)
    # Sort the elements if needed
    if sort_by is not None:
        reverse_sort = sort_order == "desc"
        # If it is a queryset, we can use the order_by method
        if hasattr(overview["elements"], "order_by"):
            if reverse_sort:
                overview["elements"] = overview["elements"].order_by(f"-{sort_by}")
            else:
                overview["elements"] = overview["elements"].order_by(sort_by)
        else:
            overview["elements"].sort(key=lambda x: _get_attr(x, sort_by), reverse=reverse_sort)
    
    # We extract the first field of the normal table because then we can not center the first column in jinja
    overview["first_t_heading_dict"] = overview["heading_dicts"].pop(0)
    for i in range(len(overview["elements"])):
        element = overview["elements"][i]
        row = {}
        row["first_field"] = _get_attr(element, overview["t_keys"][0])
        row_content = []
        for j in range(1, len(overview["t_keys"])):
            key = overview["t_keys"][j]
            current_element = element
            while "." in key:
                split_key = key.split(".")
                key = ".".join(split_key[1:])
                current_element = _get_attr(current_element, split_key[0])
            row_content.append(_get_attr(current_element, key))
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
    elif type(value).__name__ == "datetime":
        value = value.strftime("%Y-%m-%d %H:%M:%S")
    elif type(value).__name__ == "date":
        value = value.strftime("%Y-%m-%d")

    # Check if its a email:
    if isinstance(value, str) and "@" in value and "." in value:
        value = f'<a href="mailto:{value}">{value}</a>'

    # Check if its a url:
    if isinstance(value, str) and (value.startswith("http://") or value.startswith("https://")):
        value = f'<a href="{value}" target="_blank" rel="noopener noreferrer">{value}</a>'
    
    return value
        
def message(request, message : str, url_name : str = "", url_args : list = []):
    if url_name == "":
        url_name = "index"
    url = "/"
    try:
        url = reverse(url_name, args=url_args)
    except Exception as e:
        if url_name.startswith("/"):
            url = url_name
        print(f"Could not reverse url {url_name} with args {url_args}: {e}")
    return render(request, "lac/message.html", {"message": message, "url": url})


def get_2column_table(data: dict):
    """
    Returns a 2 column table with the data in html format.
    The data should be a dictionary with the keys as the first column and the values as the second column.
    """
    table = "<table>"
    for key, value in data.items():
        field2 = _get_attr(data, key)
        field2 = str(field2).replace("\n", "<br>")
        table += f"<tr><td><b>{key}</b></td><td>{field2}</td></tr>"
    table += "</table>"
    return table
    