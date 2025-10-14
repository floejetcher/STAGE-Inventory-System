import streamlit as st
import pandas as pd
from inventory_db import init_db, add_item, update_item, list_items, get_item, set_in_use, get_locations, get_tags, get_categories, delete_item, add_location

st.set_page_config(page_title="STAGE Inventory", page_icon="🎭", layout="wide")

# Ensure DB exists
init_db()

# Presets
def current_locations():
    # Pull from DB each run to include any user-added locations
    locs = get_locations()
    if not locs:
        return [
            "West Campus Basement Storage",
            "East Campus Basement Storage",
            "East Campus Theatre Closet",
        ]
    return locs

PRESET_TAGS = [
    "Lights",
    "Sound",
    "Set",
    "Props",
    "Costumes",
    "General Tech",
    "Theatre Class Usage",
]

PRESET_CATEGORIES = [
    "Props",
    "Costumes",
    "Set Pieces",
    "Lighting",
    "Sound",
    "Equipment",
    "General",
]

# Sidebar navigation
st.sidebar.title("STAGE Inventory")
page = st.sidebar.radio("Navigate", ["Browse & Filter", "Add Item", "Edit Item", "Location Report"])  # SC1, SC2, SC4, SC5

# (Filters moved into main Browse & Filter page)


# Optional utilities
with st.sidebar.expander("Utilities"):
    if st.button("Load sample items"):
        sample = [
            ("Mason jar", "Props", "Props", "West Campus Basement Storage", False),
            ("Top Hat", "Costumes", "Costumes", "East Campus Theatre Closet", False),
            ("XLR Cable 25ft", "Equipment", "Sound", "East Campus Basement Storage", True),
            ("LED Par Can", "Lighting", "Lights", "West Campus Basement Storage", False),
            ("Sawhorse", "Set Pieces", "Set", "East Campus Basement Storage", False),
        ]
        for n, c, t, l, u in sample:
            add_item(n, c, t, l, u)
        st.success("Sample items added.")

    st.divider()
    new_loc = st.text_input("Add a new location")
    if st.button("Add Location"):
        if not new_loc.strip():
            st.warning("Please enter a location name.")
        else:
            add_location(new_loc)
            st.success(f"Added location: {new_loc.strip()}")
            st.rerun()


def render_table(rows):
    if not rows:
        st.info("No items match the current filters.")
        return
    df = pd.DataFrame(rows)
    df = df.rename(columns={"category": "Category", "crew_tag": "Crew Tag", "location": "Location", "in_use": "In Use", "name": "Name", "id": "ID"})
    df = df[["ID", "Name", "Category", "Crew Tag", "Location", "In Use"]]
    st.dataframe(df, use_container_width=True, hide_index=True)


if page == "Browse & Filter":  # SC4
    st.header("Browse & Filter")
    st.caption("Search, filter by crew tag/location, and sort results.")

    with st.container():
        c1, c2, c3, c4, c5 = st.columns([3, 3, 3, 3, 2])
        with c1:
            search = st.text_input("Search by name")
        with c2:
            selected_categories = st.multiselect("Categories", options=PRESET_CATEGORIES)
        with c3:
            selected_tags = st.multiselect("Crew tags", options=PRESET_TAGS)
        with c4:
            selected_locations = st.multiselect("Locations", options=current_locations())
        with c5:
            in_use_filter = st.selectbox("In use?", options=["Any", "Yes", "No"])

    filter_kwargs = {
        "name_query": search or None,
        "categories": selected_categories or None,
        "tags": selected_tags or None,
        "locations": selected_locations or None,
        "in_use": None if in_use_filter == "Any" else (in_use_filter == "Yes"),
    }

    sort_by = st.selectbox("Sort by", options=["Name", "Category", "Crew Tag", "Location", "In Use"]) 
    rows = list_items(**filter_kwargs)

    # Sort in Python for simplicity
    key_map = {
        "Name": lambda r: r["name"].lower(),
        "Category": lambda r: r["category"].lower(),
        "Crew Tag": lambda r: r["crew_tag"].lower(),
        "Location": lambda r: r["location"].lower(),
        "In Use": lambda r: (not r["in_use"])  # False before True
    }
    rows.sort(key=key_map[sort_by])
    render_table(rows)


elif page == "Add Item":  # SC1
    st.header("Add a New Item")

    with st.form("add_item_form", clear_on_submit=True):
        name = st.text_input("Item name", placeholder="e.g., Mason jar, top hat, XLR cable")
        category = st.selectbox("Category", options=PRESET_CATEGORIES, index=PRESET_CATEGORIES.index("General"))
        crew_tag = st.selectbox("Crew tag", options=PRESET_TAGS, index=PRESET_TAGS.index("Props"))
        location = st.selectbox("Location", options=current_locations())
        in_use = st.checkbox("Currently in use?", value=False)
        submitted = st.form_submit_button("Add Item")

        if submitted:
            if not name.strip():
                st.error("Name is required.")
            else:
                add_item(name=name.strip(), category=category, crew_tag=crew_tag, location=location, in_use=in_use)
                st.success(f"Added '{name}' to inventory.")


elif page == "Edit Item":  # SC2
    st.header("Edit Item")

    rows = list_items()
    if not rows:
        st.info("No items yet. Add your first item in the 'Add Item' page.")
    else:
        options = {f"#{r['id']} — {r['name']} ({r['category']}) [{r['crew_tag']}] @ {r['location']}": r['id'] for r in rows}
        selection = st.selectbox("Select an item to edit", options=list(options.keys()))
        item_id = options[selection]
        item = get_item(item_id)

        with st.form("edit_item_form"):
            new_name = st.text_input("Item name", value=item["name"])
            new_category = st.selectbox("Category", options=PRESET_CATEGORIES, index=PRESET_CATEGORIES.index(item["category"]) if item["category"] in PRESET_CATEGORIES else 0)
            new_crew_tag = st.selectbox("Crew tag", options=PRESET_TAGS, index=PRESET_TAGS.index(item["crew_tag"]) if item["crew_tag"] in PRESET_TAGS else 0)
            locs = current_locations()
            new_location = st.selectbox("Location", options=locs, index=locs.index(item["location"]) if item["location"] in locs else 0)
            new_in_use = st.checkbox("Currently in use?", value=item["in_use"]) 
            submitted = st.form_submit_button("Save Changes")

            if submitted:
                if not new_name.strip():
                    st.error("Name is required.")
                else:
                    update_item(item_id, name=new_name.strip(), category=new_category, crew_tag=new_crew_tag, location=new_location, in_use=new_in_use)
                    st.success("Item updated.")

        # Delete item section
        with st.expander("Danger zone: Delete this item"):
            with st.form("delete_item_form"):
                confirm = st.checkbox("Yes, permanently delete this item")
                del_submit = st.form_submit_button("Delete Item", type="primary")
                if del_submit:
                    if confirm:
                        delete_item(item_id)
                        st.success("Item deleted.")
                        st.rerun()
                    else:
                        st.warning("Please confirm deletion by checking the box.")


elif page == "Location Report":  # SC5
    st.header("Location Report")
    st.caption("List items in a location; mark items temporarily in use.")

    location = st.selectbox("Choose a location", options=current_locations())
    show_in_use = st.checkbox("Show only items currently in use", value=False)

    rows = list_items(locations=[location], in_use=True if show_in_use else None)

    if rows:
        for r in rows:
            cols = st.columns([6, 2])
            cols[0].write(f"#{r['id']} — {r['name']} ({r['category']}) [{r['crew_tag']}] — In use: {'Yes' if r['in_use'] else 'No'}")
            toggled = cols[1].toggle("Toggle In Use", value=r["in_use"], key=f"toggle_{r['id']}")
            if toggled != r["in_use"]:
                set_in_use(r["id"], toggled)
                st.rerun()

        # Download CSV
        df = pd.DataFrame(rows)
        csv = df.to_csv(index=False)
        st.download_button("Download CSV", data=csv, file_name=f"location_report_{location.replace(' ', '_')}.csv", mime="text/csv")
    else:
        st.info("No items found for this selection.")
