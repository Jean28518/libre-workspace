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
    for element in overview["elements"]:
        row_content = []
        for key in overview["t_keys"]:
            row_content.append(element[key])
        row = {
            "content": row_content,
        }
        if overview.get("edit_url_name", None) is not None:
            row["edit_url"] = reverse(overview["edit_url_name"], args=[element[overview["element_url_key"]]])
        if overview.get("delete_url_name", None) is not None:
            row["delete_url"] = reverse(overview["delete_url_name"], args=[element[overview["element_url_key"]]])
        overview["table_content"].append(row)
    
    return overview
        
        
def message(request, message : str, url_name : str = "", url_args : list = []):
    if url_name == "":
        url_name = "index"
    return render(request, "lac/message.html", {"message": message, "url": reverse(url_name, args=[])})