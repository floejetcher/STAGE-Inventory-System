import streamlit as st
import pandas as pd
import os
from inventory_db import init_db, add_item, update_item, list_items, get_item, set_in_use, get_locations, get_tags, get_categories, delete_item, add_location
from auth import login, logout, is_admin, current_user, current_role
from announcements import load_announcements, add_announcement, delete_announcement
from item_images import get_item_image, has_item_image, save_item_image, remove_item_image

st.set_page_config(page_title="STAGE Inventory", page_icon="🎭", layout="wide")

# Make select dropdowns taller and scrollable
st.markdown("""
<style>
/* Increase dropdown (select) menu height and ensure scrolling */
div[data-baseweb="select"] div[role="listbox"] {
  max-height: 420px;
}
</style>
""", unsafe_allow_html=True)

# Ensure DB exists
init_db()

# Require authentication before showing the app
if not login():
    st.stop()

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

# Sidebar navigation (role-aware)
st.sidebar.image("logo.png", width=216)  # small logo above the title
st.sidebar.title("STAGE Inventory")
st.sidebar.caption(f"Signed in as: {current_user()} ({current_role()})")

if st.sidebar.button("Log out"):
    logout()
    st.rerun()

# Moved announcements below the navigation radio
guest_pages = ["Browse & Filter", "Location Report"]
admin_pages = guest_pages + ["Add Item", "Edit Item"]
available_pages = admin_pages if is_admin() else guest_pages

page = st.sidebar.radio("Navigate", available_pages)  # SC1, SC2, SC4, SC5

# STAGE Announcements (in sidebar, now below navigation)
with st.sidebar.expander("STAGE Announcements", expanded=True):
    anns = load_announcements(limit=5)
    if anns:
        for a in anns:
            st.markdown(f"- {a['text']}  \n  ⸺ {a.get('author', 'Unknown')}")
            if is_admin():
                if st.button("Delete", key=f"del_ann_{a['id']}"):
                    delete_announcement(a["id"])
                    st.rerun()
            st.markdown("---")
    else:
        st.caption("No announcements yet.")

    if is_admin():
        with st.form("post_announcement_sidebar", clear_on_submit=True):
            new_text = st.text_input("Post an update", placeholder="Short announcement...")
            submitted = st.form_submit_button("Post")
            if submitted:
                if new_text.strip():
                    add_announcement(new_text.strip(), current_user() or "Admin")
                    st.rerun()
                else:
                    st.warning("Enter some text to post.")

# Admin-only utilities
if is_admin():
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

def render_rows_with_image_buttons(rows):
    if not rows:
        st.info("No items match the current filters.")
        return

    # Header row
    h = st.columns([1.2, 3.2, 2.2, 2.0, 2.2, 1.0, 1.4])
    h[0].markdown("**ID**")
    h[1].markdown("**Name**")
    h[2].markdown("**Category**")
    h[3].markdown("**Crew Tag**")
    h[4].markdown("**Location**")
    h[5].markdown("**In Use**")
    h[6].markdown("**Action**")

    for r in rows:
        cols = st.columns([1.2, 3.2, 2.2, 2.0, 2.2, 1.0, 1.4])
        cols[0].write(r["id"])
        cols[1].write(r["name"])
        cols[2].write(r["category"])
        cols[3].write(r["crew_tag"])
        cols[4].write(r["location"])
        cols[5].write("Yes" if r["in_use"] else "No")

        # Toggle show/hide image per item
        flag_key = f"show_img_{r['id']}"
        shown = st.session_state.get(flag_key, False)

        if has_item_image(r["id"]):
            label = "Hide Image" if st.session_state.get(flag_key := f"show_img_{r['id']}", False) else "View Image"
            if cols[6].button(label, key=f"view_image_btn_{r['id']}"):
                st.session_state[flag_key] = not st.session_state.get(flag_key, False)
                st.rerun()
        else:
            cols[6].empty()

        if st.session_state.get(flag_key):
            img_path = get_item_image(r["id"])
            if img_path:
                st.image(img_path, use_container_width=True, caption=f"#{r['id']} — {r['name']}")

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

    key_map = {
        "Name": lambda r: r["name"].lower(),
        "Category": lambda r: r["category"].lower(),
        "Crew Tag": lambda r: r["crew_tag"].lower(),
        "Location": lambda r: r["location"].lower(),
        "In Use": lambda r: (not r["in_use"])
    }
    rows.sort(key=key_map[sort_by])

    render_rows_with_image_buttons(rows)

elif page == "Add Item":  # SC1 (admin only)
    if not is_admin():
        st.warning("Not authorized.")
    else:
        st.header("Add a New Item")
        with st.form("add_item_form", clear_on_submit=True):
            name = st.text_input("Item name", placeholder="e.g., Mason jar, top hat, XLR cable")
            category = st.selectbox("Category", options=PRESET_CATEGORIES, index=PRESET_CATEGORIES.index("General"))
            crew_tag = st.selectbox("Crew tag", options=PRESET_TAGS, index=PRESET_TAGS.index("Props"))
            location = st.selectbox("Location", options=current_locations())
            in_use = st.checkbox("Currently in use?", value=False)
            image_file = st.file_uploader("Optional image", type=["png", "jpg", "jpeg", "webp"])
            submitted = st.form_submit_button("Add Item")

            if submitted:
                if not name.strip():
                    st.error("Name is required.")
                else:
                    # Add item
                    add_item(name=name.strip(), category=category, crew_tag=crew_tag, location=location, in_use=in_use)
                    st.success(f"Added '{name}' to inventory.")

                    # Find the recently added item id by matching attributes (pick max id)
                    rows = list_items(name_query=name.strip(), categories=[category], tags=[crew_tag], locations=[location], in_use=in_use)
                    if rows:
                        new_id = max(rows, key=lambda r: r["id"])["id"]
                        if image_file is not None:
                            save_item_image(new_id, image_file)
                            st.success("Image saved for the new item.")

elif page == "Edit Item":  # SC2 (admin only)
    if not is_admin():
        st.warning("Not authorized.")
    else:
        st.header("Edit Item")

        rows = list_items()
        if not rows:
            st.info("No items yet. Add your first item in the 'Add Item' page.")
        else:
            options = {f"#{r['id']} — {r['name']} ({r['category']}) [{r['crew_tag']}] @ {r['location']}": r['id'] for r in rows}
            selection = st.selectbox("Select an item to edit", options=list(options.keys()))
            item_id = options[selection]
            item = get_item(item_id)

            current_img = get_item_image(item_id)
            with st.form("edit_item_form"):
                new_name = st.text_input("Item name", value=item["name"])
                new_category = st.selectbox("Category", options=PRESET_CATEGORIES, index=PRESET_CATEGORIES.index(item["category"]) if item["category"] in PRESET_CATEGORIES else 0)
                new_crew_tag = st.selectbox("Crew tag", options=PRESET_TAGS, index=PRESET_TAGS.index(item["crew_tag"]) if item["crew_tag"] in PRESET_TAGS else 0)
                locs = current_locations()
                new_location = st.selectbox("Location", options=locs, index=locs.index(item["location"]) if item["location"] in locs else 0)
                new_in_use = st.checkbox("Currently in use?", value=item["in_use"]) 
                st.markdown("---")
                st.caption("Item image")
                if current_img:
                    st.image(current_img, caption="Current image", width=220)
                remove_img = st.checkbox("Remove image", value=False)
                replace_img = st.file_uploader("Replace with new image (optional)", type=["png", "jpg", "jpeg", "webp"])
                submitted = st.form_submit_button("Save Changes")

                if submitted:
                    if not new_name.strip():
                        st.error("Name is required.")
                    else:
                        update_item(item_id, name=new_name.strip(), category=new_category, crew_tag=new_crew_tag, location=new_location, in_use=new_in_use)
                        # Handle image ops
                        if remove_img and current_img:
                            remove_item_image(item_id)
                        if replace_img is not None:
                            save_item_image(item_id, replace_img)
                        st.success("Item updated.")
                        st.rerun()

            # Delete item section
            with st.expander("Danger zone: Delete this item"):
                with st.form("delete_item_form"):
                    confirm = st.checkbox("Yes, permanently delete this item")
                    del_submit = st.form_submit_button("Delete Item", type="primary")
                    if del_submit:
                        if confirm:
                            # Remove image (if any) then the item
                            remove_item_image(item_id)
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
            cols = st.columns([6, 1.5, 1.5])
            cols[0].write(f"#{r['id']} — {r['name']} ({r['category']}) [{r['crew_tag']}] — In use: {'Yes' if r['in_use'] else 'No'}")
            toggled = cols[1].toggle("Toggle In Use", value=r["in_use"], key=f"toggle_{r['id']}")
            if toggled != r["in_use"]:
                set_in_use(r["id"], toggled)
                st.rerun()

            if has_item_image(r["id"]):
                flag_key = f"show_img_report_{r['id']}"
                shown = st.session_state.get(flag_key, False)
                label = "Hide Image" if shown else "View Image"
                if cols[2].button(label, key=f"report_img_btn_{r['id']}"):
                    st.session_state[flag_key] = not shown
                    st.rerun()

                if st.session_state.get(flag_key):
                    img_path = get_item_image(r["id"])
                    if img_path:
                        st.image(img_path, use_container_width=True, caption=f"#{r['id']} — {r['name']}")

        df = pd.DataFrame(rows)
        csv = df.to_csv(index=False)
        st.download_button("Download CSV", data=csv, file_name=f"location_report_{location.replace(' ', '_')}.csv", mime="text/csv")
    else:
        st.info("No items found for this selection.")

# Footer: bottom-left credit
st.markdown(
    """
    <style>
      .stAppFooter {
        position: fixed;
        left: 0.75rem;
        bottom: 0.5rem;
        font-size: 0.85rem;
        color: rgba(49, 51, 63, 0.6);
        z-index: 9999;
      }
    </style>
    <div class="stAppFooter">Application Made By Joe Fletcher</div>
    """,
    unsafe_allow_html=True,
)
