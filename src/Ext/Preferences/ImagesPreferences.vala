[GtkTemplate (ui = "/org/gnome/gthumb/ui/images-preferences.ui")]
public class Gth.ImagesPreferences : Adw.NavigationPage {
	construct {
		settings = new GLib.Settings (GTHUMB_IMAGES_SCHEMA);
		constructing = true;
		scroll_action.selected = get_action_index (settings.get_enum (PREF_IMAGE_SCROLL_ACTION));
		drag_action.selected = settings.get_boolean (PREF_IMAGE_DRAG_TO_ZOOM) ? 1 : 0;
		constructing = false;
	}

	[GtkCallback]
	void on_drag_action_selected (Object obj, ParamSpec param) {
		if (constructing) {
			return;
		}
		settings.set_boolean (PREF_IMAGE_DRAG_TO_ZOOM, drag_action.selected == 1);
	}

	[GtkCallback]
	void on_scroll_action_selected (Object obj, ParamSpec param) {
		if (constructing) {
			return;
		}
		var idx = scroll_action.selected;
		settings.set_enum (PREF_IMAGE_SCROLL_ACTION, ACTION[idx]);
	}

	uint get_action_index (ScrollAction value) {
		uint idx = 0;
		foreach (unowned var item in ACTION) {
			if (value == item) {
				return idx;
			}
			idx++;
		}
		return 0;
	}

	[GtkChild] unowned Adw.ComboRow scroll_action;
	[GtkChild] unowned Adw.ComboRow drag_action;
	GLib.Settings settings;
	bool constructing;

	const ScrollAction[] ACTION = {
		ScrollAction.CHANGE_ZOOM,
		ScrollAction.CHANGE_FILE,
	};
}
