/*
THIS IS A GENERATED/BUNDLED FILE BY ESBUILD
if you want to view the source, please visit the github repository of this plugin
*/

var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// main.ts
var main_exports = {};
__export(main_exports, {
  FileSuggest: () => FileSuggest,
  default: () => PinnedNotesPlugin,
  trimFile: () => trimFile
});
module.exports = __toCommonJS(main_exports);
var import_obsidian = require("obsidian");

// node_modules/uuid/dist/esm-browser/rng.js
var getRandomValues;
var rnds8 = new Uint8Array(16);
function rng() {
  if (!getRandomValues) {
    getRandomValues = typeof crypto !== "undefined" && crypto.getRandomValues && crypto.getRandomValues.bind(crypto);
    if (!getRandomValues) {
      throw new Error("crypto.getRandomValues() not supported. See https://github.com/uuidjs/uuid#getrandomvalues-not-supported");
    }
  }
  return getRandomValues(rnds8);
}

// node_modules/uuid/dist/esm-browser/stringify.js
var byteToHex = [];
for (let i = 0; i < 256; ++i) {
  byteToHex.push((i + 256).toString(16).slice(1));
}
function unsafeStringify(arr, offset = 0) {
  return byteToHex[arr[offset + 0]] + byteToHex[arr[offset + 1]] + byteToHex[arr[offset + 2]] + byteToHex[arr[offset + 3]] + "-" + byteToHex[arr[offset + 4]] + byteToHex[arr[offset + 5]] + "-" + byteToHex[arr[offset + 6]] + byteToHex[arr[offset + 7]] + "-" + byteToHex[arr[offset + 8]] + byteToHex[arr[offset + 9]] + "-" + byteToHex[arr[offset + 10]] + byteToHex[arr[offset + 11]] + byteToHex[arr[offset + 12]] + byteToHex[arr[offset + 13]] + byteToHex[arr[offset + 14]] + byteToHex[arr[offset + 15]];
}

// node_modules/uuid/dist/esm-browser/native.js
var randomUUID = typeof crypto !== "undefined" && crypto.randomUUID && crypto.randomUUID.bind(crypto);
var native_default = {
  randomUUID
};

// node_modules/uuid/dist/esm-browser/v4.js
function v4(options, buf, offset) {
  if (native_default.randomUUID && !buf && !options) {
    return native_default.randomUUID();
  }
  options = options || {};
  const rnds = options.random || (options.rng || rng)();
  rnds[6] = rnds[6] & 15 | 64;
  rnds[8] = rnds[8] & 63 | 128;
  if (buf) {
    offset = offset || 0;
    for (let i = 0; i < 16; ++i) {
      buf[offset + i] = rnds[i];
    }
    return buf;
  }
  return unsafeStringify(rnds);
}
var v4_default = v4;

// main.ts
var PinnedNote = class {
  constructor(title, path, icon) {
    this.id = v4_default();
    this.icon = icon;
    this.path = path;
    this.title = title;
  }
};
var DEFAULT_SETTINGS = {
  pinnedNotes: []
};
var PinnedNotesPlugin = class extends import_obsidian.Plugin {
  async onload() {
    await this.loadSettings();
    this.addSettingTab(new SettingTab(this.app, this));
  }
  async addPinnedNote(note) {
    this.settings.pinnedNotes.push(note);
    await this.saveSettings();
    await this.loadSettings();
  }
  async removePinnedNote(noteId) {
    const noteIndex = this.settings.pinnedNotes.findIndex((note) => note.id === noteId);
    delete this.settings.pinnedNotes[noteIndex];
    this.settings.pinnedNotes.splice(noteIndex, 1);
    await this.saveSettings();
    await this.loadSettings();
  }
  async loadSettings() {
    var _a;
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
    (_a = this.ribbonIcons) == null ? void 0 : _a.forEach((ribbonIcon, index) => {
      ribbonIcon.remove();
      delete this.ribbonIcons[index];
    });
    this.ribbonIcons = this.settings.pinnedNotes.map(
      (note) => this.addRibbonIcon(
        note.icon === "" ? "file" : note.icon,
        note.title,
        async (e) => {
          await this.app.workspace.openLinkText(
            note.path,
            "",
            e.button == 1 || e.button == 2 || import_obsidian.Keymap.isModifier(e, "Mod")
          );
        }
      )
    );
  }
  async saveSettings() {
    await this.saveData(this.settings);
  }
};
var SettingTab = class extends import_obsidian.PluginSettingTab {
  constructor(app, plugin) {
    super(app, plugin);
    this.plugin = plugin;
  }
  display() {
    const { containerEl } = this;
    containerEl.empty();
    let isCanBeAddedNewNote = true;
    let title = "";
    let path = "";
    let icon = "";
    let changedTitle;
    let changedPath;
    let changedIcon;
    const addNoteButton = new import_obsidian.Setting(containerEl).setName("Add pinned note").setDesc(`Provide: 1) file's name that will be displayed on hover 2) path to this file, e.g Folder1/File1 3) Icon name from lucide.dev; if icon won't be provided, default icon "file" will be placed instead. RESTART OBSIDIAN AFTER CHANGES`);
    isCanBeAddedNewNote && addNoteButton.addButton((button) => {
      button.setIcon("plus").onClick(
        () => {
          isCanBeAddedNewNote = false;
          this.display();
          new import_obsidian.Setting(containerEl).setName("File").addText(
            (text) => text.setPlaceholder("Title").onChange((value) => title = value)
          ).addText(
            (text) => {
              new FileSuggest(this.app, text.inputEl);
              text.setPlaceholder("Path").onChange((value) => path = value);
            }
          ).addText(
            (text) => text.setPlaceholder("Icon(optional)").onChange((value) => icon = value)
          ).addButton((button2) => button2.setIcon("save").onClick(
            async () => {
              if (title.length !== 0 && path.length !== 0) {
                await this.plugin.addPinnedNote(new PinnedNote(title, path, icon));
                isCanBeAddedNewNote = true;
                this.display();
              } else {
                new import_obsidian.Notice("Provide title and path");
              }
            }
          ));
        }
      );
    });
    this.plugin.settings.pinnedNotes.forEach((note, index) => {
      new import_obsidian.Setting(containerEl).setName("File " + (index + 1)).addText(
        (text) => text.setPlaceholder("Title").setValue(note.title).onChange(async (value) => {
          changedTitle = value;
        })
      ).addText(
        (text) => {
          new FileSuggest(this.app, text.inputEl);
          text.setPlaceholder("Path").setValue(note.path).onChange(async (value) => {
            changedPath = value;
          });
        }
      ).addText(
        (text) => text.setPlaceholder("Icon(optional)").setValue(note.icon).onChange(async (value) => {
          changedIcon = value;
        })
      ).addButton(
        (button) => button.setIcon("save").onClick(
          async () => {
            if ((changedTitle === void 0 || changedTitle === note.title) && (changedPath === void 0 || changedPath === note.path) && (changedIcon === void 0 || changedIcon === note.icon)) {
              new import_obsidian.Notice("Provide any data");
              return;
            }
            if (changedTitle !== void 0) {
              if (changedTitle.length !== 0) {
                note.title = changedTitle;
                changedTitle = void 0;
              } else
                new import_obsidian.Notice("Provide title");
            }
            if (changedPath !== void 0) {
              if (changedPath.length !== 0) {
                note.path = changedPath;
                changedPath = void 0;
              } else
                new import_obsidian.Notice("Provide path");
            }
            if (changedIcon !== void 0) {
              note.icon = changedIcon;
              changedIcon = void 0;
            }
            await this.plugin.saveSettings();
            await this.plugin.loadSettings();
            this.display();
          }
        )
      ).addButton((button) => button.setIcon("trash-2").setWarning().onClick(
        async () => {
          await this.plugin.removePinnedNote(note.id);
          this.display();
        }
      ));
    });
  }
};
var FileSuggest = class extends import_obsidian.AbstractInputSuggest {
  getSuggestions(inputStr) {
    const abstractFiles = this.app.vault.getAllLoadedFiles();
    const files = [];
    const inputLower = inputStr.toLowerCase();
    abstractFiles.forEach((file) => {
      if (file instanceof import_obsidian.TFile && ["md", "canvas"].contains(file.extension) && file.path.toLowerCase().contains(inputLower)) {
        files.push(file);
      }
    });
    return files;
  }
  renderSuggestion(file, el) {
    if (file.extension == "md") {
      el.setText(trimFile(file));
    } else {
      el.setText(file.path.slice(0, -7));
      el.insertAdjacentHTML(
        "beforeend",
        `<div class="nav-file-tag" style="display:inline-block;vertical-align:middle">canvas</div>`
      );
    }
  }
  selectSuggestion(file) {
    this.textInputEl.value = trimFile(file);
    this.textInputEl.trigger("input");
    this.close();
  }
};
function trimFile(file) {
  if (!file)
    return "";
  return file.extension == "md" ? file.path.slice(0, -3) : file.path;
}
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsibWFpbi50cyIsICJub2RlX21vZHVsZXMvdXVpZC9kaXN0L2VzbS1icm93c2VyL3JuZy5qcyIsICJub2RlX21vZHVsZXMvdXVpZC9kaXN0L2VzbS1icm93c2VyL3N0cmluZ2lmeS5qcyIsICJub2RlX21vZHVsZXMvdXVpZC9kaXN0L2VzbS1icm93c2VyL25hdGl2ZS5qcyIsICJub2RlX21vZHVsZXMvdXVpZC9kaXN0L2VzbS1icm93c2VyL3Y0LmpzIl0sCiAgInNvdXJjZXNDb250ZW50IjogWyJpbXBvcnQge1xyXG5cdEFic3RyYWN0SW5wdXRTdWdnZXN0LFxyXG5cdEFwcCxcclxuXHRJY29uTmFtZSxcclxuXHRLZXltYXAsXHJcblx0Tm90aWNlLFxyXG5cdFBsdWdpbixcclxuXHRQbHVnaW5TZXR0aW5nVGFiLFxyXG5cdFNldHRpbmcsXHJcblx0VEFic3RyYWN0RmlsZSxcclxuXHRURmlsZVxyXG59IGZyb20gXCJvYnNpZGlhblwiO1xyXG5pbXBvcnQge3Y0IGFzIHV1aWR2NH0gZnJvbSBcInV1aWRcIjtcclxuXHJcbmNsYXNzIFBpbm5lZE5vdGUge1xyXG5cdGlkOiBudW1iZXI7XHJcblx0aWNvbjogSWNvbk5hbWU7XHJcblx0cGF0aDogc3RyaW5nO1xyXG5cdHRpdGxlOiBzdHJpbmc7XHJcblxyXG5cclxuXHRjb25zdHJ1Y3RvcihcclxuXHRcdHRpdGxlOiBzdHJpbmcsXHJcblx0XHRwYXRoOiBzdHJpbmcsXHJcblx0XHRpY29uOiBJY29uTmFtZVxyXG5cdCkge1xyXG5cdFx0dGhpcy5pZCA9IHV1aWR2NCgpXHJcblx0XHR0aGlzLmljb24gPSBpY29uO1xyXG5cdFx0dGhpcy5wYXRoID0gcGF0aDtcclxuXHRcdHRoaXMudGl0bGUgPSB0aXRsZTtcclxuXHR9XHJcbn1cclxuXHJcbmV4cG9ydCBpbnRlcmZhY2UgSVBpbm5lZE5vdGVzUGx1Z2luU2V0dGluZ3Mge1xyXG5cdHBpbm5lZE5vdGVzOiBQaW5uZWROb3RlW11cclxufVxyXG5cclxuY29uc3QgREVGQVVMVF9TRVRUSU5HUzogSVBpbm5lZE5vdGVzUGx1Z2luU2V0dGluZ3MgPSB7XHJcblx0cGlubmVkTm90ZXM6IFtdXHJcbn1cclxuXHJcbmV4cG9ydCBkZWZhdWx0IGNsYXNzIFBpbm5lZE5vdGVzUGx1Z2luIGV4dGVuZHMgUGx1Z2luIHtcclxuXHRzZXR0aW5nczogSVBpbm5lZE5vdGVzUGx1Z2luU2V0dGluZ3NcclxuXHRyaWJib25JY29uczogSFRNTEVsZW1lbnRbXVxyXG5cclxuXHRhc3luYyBvbmxvYWQoKSB7XHJcblx0XHRhd2FpdCB0aGlzLmxvYWRTZXR0aW5ncygpO1xyXG5cdFx0dGhpcy5hZGRTZXR0aW5nVGFiKG5ldyBTZXR0aW5nVGFiKHRoaXMuYXBwLCB0aGlzKSlcclxuXHR9XHJcblxyXG5cdGFzeW5jIGFkZFBpbm5lZE5vdGUobm90ZTogUGlubmVkTm90ZSkge1xyXG5cdFx0dGhpcy5zZXR0aW5ncy5waW5uZWROb3Rlcy5wdXNoKG5vdGUpXHJcblx0XHRhd2FpdCB0aGlzLnNhdmVTZXR0aW5ncygpXHJcblx0XHRhd2FpdCB0aGlzLmxvYWRTZXR0aW5ncygpXHJcblx0fVxyXG5cclxuXHRhc3luYyByZW1vdmVQaW5uZWROb3RlKG5vdGVJZDogbnVtYmVyKSB7XHJcblx0XHRjb25zdCBub3RlSW5kZXggPSB0aGlzLnNldHRpbmdzLnBpbm5lZE5vdGVzLmZpbmRJbmRleCgobm90ZSkgPT4gbm90ZS5pZCA9PT0gbm90ZUlkKVxyXG5cdFx0ZGVsZXRlIHRoaXMuc2V0dGluZ3MucGlubmVkTm90ZXNbbm90ZUluZGV4XVxyXG5cdFx0dGhpcy5zZXR0aW5ncy5waW5uZWROb3Rlcy5zcGxpY2Uobm90ZUluZGV4LCAxKVxyXG5cdFx0YXdhaXQgdGhpcy5zYXZlU2V0dGluZ3MoKVxyXG5cdFx0YXdhaXQgdGhpcy5sb2FkU2V0dGluZ3MoKVxyXG5cdH1cclxuXHJcblxyXG5cdGFzeW5jIGxvYWRTZXR0aW5ncygpIHtcclxuXHRcdHRoaXMuc2V0dGluZ3MgPSBPYmplY3QuYXNzaWduKHt9LCBERUZBVUxUX1NFVFRJTkdTLCBhd2FpdCB0aGlzLmxvYWREYXRhKCkpO1xyXG5cdFx0dGhpcy5yaWJib25JY29ucz8uZm9yRWFjaCgocmliYm9uSWNvbiwgaW5kZXgpID0+IHtcclxuXHRcdFx0cmliYm9uSWNvbi5yZW1vdmUoKVxyXG5cdFx0XHRkZWxldGUgdGhpcy5yaWJib25JY29uc1tpbmRleF1cclxuXHRcdH0pXHJcblx0XHR0aGlzLnJpYmJvbkljb25zID0gdGhpcy5zZXR0aW5ncy5waW5uZWROb3Rlcy5tYXAoKG5vdGUpID0+XHJcblx0XHRcdHRoaXMuYWRkUmliYm9uSWNvbihcclxuXHRcdFx0XHRub3RlLmljb24gPT09IFwiXCIgPyBcImZpbGVcIiA6IG5vdGUuaWNvbixcclxuXHRcdFx0XHRub3RlLnRpdGxlLFxyXG5cdFx0XHRcdGFzeW5jIChlKSA9PiB7XHJcblx0XHRcdFx0XHRhd2FpdCB0aGlzLmFwcC53b3Jrc3BhY2Uub3BlbkxpbmtUZXh0KFxyXG5cdFx0XHRcdFx0XHRub3RlLnBhdGgsXHJcblx0XHRcdFx0XHRcdFwiXCIsXHJcblx0XHRcdFx0XHRcdGUuYnV0dG9uID09IDEgfHwgZS5idXR0b24gPT0gMiB8fCBLZXltYXAuaXNNb2RpZmllcihlLCBcIk1vZFwiKVxyXG5cdFx0XHRcdFx0KTtcclxuXHRcdFx0XHR9XHJcblx0XHRcdClcclxuXHRcdClcclxuXHR9XHJcblxyXG5cdGFzeW5jIHNhdmVTZXR0aW5ncygpIHtcclxuXHRcdGF3YWl0IHRoaXMuc2F2ZURhdGEodGhpcy5zZXR0aW5ncyk7XHJcblx0fVxyXG59XHJcblxyXG5jbGFzcyBTZXR0aW5nVGFiIGV4dGVuZHMgUGx1Z2luU2V0dGluZ1RhYiB7XHJcblx0cGx1Z2luOiBQaW5uZWROb3Rlc1BsdWdpblxyXG5cclxuXHRjb25zdHJ1Y3RvcihhcHA6IEFwcCwgcGx1Z2luOiBQaW5uZWROb3Rlc1BsdWdpbikge1xyXG5cdFx0c3VwZXIoYXBwLCBwbHVnaW4pO1xyXG5cdFx0dGhpcy5wbHVnaW4gPSBwbHVnaW47XHJcblx0fVxyXG5cclxuXHRkaXNwbGF5KCkge1xyXG5cdFx0Y29uc3Qge2NvbnRhaW5lckVsfSA9IHRoaXM7XHJcblx0XHRjb250YWluZXJFbC5lbXB0eSgpXHJcblx0XHRsZXQgaXNDYW5CZUFkZGVkTmV3Tm90ZSA9IHRydWVcclxuXHRcdGxldCB0aXRsZSA9IFwiXCJcclxuXHRcdGxldCBwYXRoID0gXCJcIlxyXG5cdFx0bGV0IGljb246IEljb25OYW1lID0gXCJcIlxyXG5cdFx0bGV0IGNoYW5nZWRUaXRsZTogc3RyaW5nIHwgdW5kZWZpbmVkO1xyXG5cdFx0bGV0IGNoYW5nZWRQYXRoOiBzdHJpbmcgfCB1bmRlZmluZWQ7XHJcblx0XHRsZXQgY2hhbmdlZEljb246IHN0cmluZyB8IHVuZGVmaW5lZDtcclxuXHRcdGNvbnN0IGFkZE5vdGVCdXR0b24gPSBuZXcgU2V0dGluZyhjb250YWluZXJFbClcclxuXHRcdFx0LnNldE5hbWUoXCJBZGQgcGlubmVkIG5vdGVcIilcclxuXHRcdFx0LnNldERlc2MoXCJQcm92aWRlOiAxKSBmaWxlJ3MgbmFtZSB0aGF0IHdpbGwgYmUgZGlzcGxheWVkIG9uIGhvdmVyIDIpIHBhdGggdG8gdGhpcyBmaWxlLCBlLmcgRm9sZGVyMS9GaWxlMSAzKSBJY29uIG5hbWUgZnJvbSBsdWNpZGUuZGV2OyBpZiBpY29uIHdvbid0IGJlIHByb3ZpZGVkLCBkZWZhdWx0IGljb24gXFxcImZpbGVcXFwiIHdpbGwgYmUgcGxhY2VkIGluc3RlYWQuIFJFU1RBUlQgT0JTSURJQU4gQUZURVIgQ0hBTkdFU1wiKVxyXG5cdFx0aXNDYW5CZUFkZGVkTmV3Tm90ZSAmJiBhZGROb3RlQnV0dG9uXHJcblx0XHRcdC5hZGRCdXR0b24oKGJ1dHRvbikgPT4ge1xyXG5cdFx0XHRcdGJ1dHRvbi5zZXRJY29uKFwicGx1c1wiKS5vbkNsaWNrKFxyXG5cdFx0XHRcdFx0KCkgPT4ge1xyXG5cdFx0XHRcdFx0XHRpc0NhbkJlQWRkZWROZXdOb3RlID0gZmFsc2VcclxuXHRcdFx0XHRcdFx0dGhpcy5kaXNwbGF5KClcclxuXHRcdFx0XHRcdFx0bmV3IFNldHRpbmcoY29udGFpbmVyRWwpXHJcblx0XHRcdFx0XHRcdFx0LnNldE5hbWUoXCJGaWxlXCIpXHJcblx0XHRcdFx0XHRcdFx0LmFkZFRleHQoKHRleHQpID0+IHRleHRcclxuXHRcdFx0XHRcdFx0XHRcdC5zZXRQbGFjZWhvbGRlcihcIlRpdGxlXCIpXHJcblx0XHRcdFx0XHRcdFx0XHQub25DaGFuZ2UoKHZhbHVlKSA9PiB0aXRsZSA9IHZhbHVlKVxyXG5cdFx0XHRcdFx0XHRcdClcclxuXHRcdFx0XHRcdFx0XHQuYWRkVGV4dCgodGV4dCkgPT4ge1xyXG5cdFx0XHRcdFx0XHRcdFx0bmV3IEZpbGVTdWdnZXN0KHRoaXMuYXBwLCB0ZXh0LmlucHV0RWwpO1xyXG5cdFx0XHRcdFx0XHRcdFx0XHR0ZXh0XHJcblx0XHRcdFx0XHRcdFx0XHRcdFx0LnNldFBsYWNlaG9sZGVyKFwiUGF0aFwiKVxyXG5cdFx0XHRcdFx0XHRcdFx0XHRcdC5vbkNoYW5nZSgodmFsdWUpID0+IHBhdGggPSB2YWx1ZSlcclxuXHRcdFx0XHRcdFx0XHRcdH1cclxuXHRcdFx0XHRcdFx0XHQpXHJcblx0XHRcdFx0XHRcdFx0LmFkZFRleHQoKHRleHQpID0+IHRleHRcclxuXHRcdFx0XHRcdFx0XHRcdC5zZXRQbGFjZWhvbGRlcihcIkljb24ob3B0aW9uYWwpXCIpXHJcblx0XHRcdFx0XHRcdFx0XHQub25DaGFuZ2UoKHZhbHVlKSA9PiBpY29uID0gdmFsdWUpXHJcblx0XHRcdFx0XHRcdFx0KVxyXG5cdFx0XHRcdFx0XHRcdC5hZGRCdXR0b24oKGJ1dHRvbikgPT4gYnV0dG9uLnNldEljb24oXCJzYXZlXCIpLm9uQ2xpY2soXHJcblx0XHRcdFx0XHRcdFx0XHRhc3luYyAoKSA9PiB7XHJcblx0XHRcdFx0XHRcdFx0XHRcdGlmICh0aXRsZS5sZW5ndGggIT09IDAgJiYgcGF0aC5sZW5ndGggIT09IDApIHtcclxuXHRcdFx0XHRcdFx0XHRcdFx0XHRhd2FpdCB0aGlzLnBsdWdpbi5hZGRQaW5uZWROb3RlKG5ldyBQaW5uZWROb3RlKHRpdGxlLCBwYXRoLCBpY29uKSlcclxuXHRcdFx0XHRcdFx0XHRcdFx0XHRpc0NhbkJlQWRkZWROZXdOb3RlID0gdHJ1ZVxyXG5cdFx0XHRcdFx0XHRcdFx0XHRcdHRoaXMuZGlzcGxheSgpXHJcblx0XHRcdFx0XHRcdFx0XHRcdH1cclxuXHRcdFx0XHRcdFx0XHRcdFx0ZWxzZSB7XHJcblx0XHRcdFx0XHRcdFx0XHRcdFx0bmV3IE5vdGljZShcIlByb3ZpZGUgdGl0bGUgYW5kIHBhdGhcIilcclxuXHRcdFx0XHRcdFx0XHRcdFx0fVxyXG5cdFx0XHRcdFx0XHRcdFx0fVxyXG5cdFx0XHRcdFx0XHRcdCkpXHJcblx0XHRcdFx0XHR9XHJcblx0XHRcdFx0KVxyXG5cdFx0XHR9KVxyXG5cclxuXHRcdHRoaXMucGx1Z2luLnNldHRpbmdzLnBpbm5lZE5vdGVzLmZvckVhY2goKG5vdGUsIGluZGV4KSA9PiB7XHJcblx0XHRcdG5ldyBTZXR0aW5nKGNvbnRhaW5lckVsKVxyXG5cdFx0XHRcdC5zZXROYW1lKFwiRmlsZSBcIiArIChpbmRleCArIDEpKVxyXG5cdFx0XHRcdC5hZGRUZXh0KCh0ZXh0KSA9PiB0ZXh0XHJcblx0XHRcdFx0XHQuc2V0UGxhY2Vob2xkZXIoXCJUaXRsZVwiKVxyXG5cdFx0XHRcdFx0LnNldFZhbHVlKG5vdGUudGl0bGUpXHJcblx0XHRcdFx0XHQub25DaGFuZ2UoYXN5bmMgKHZhbHVlKSA9PiB7XHJcblx0XHRcdFx0XHRcdGNoYW5nZWRUaXRsZSA9IHZhbHVlO1xyXG5cdFx0XHRcdFx0fSlcclxuXHRcdFx0XHQpXHJcblx0XHRcdFx0LmFkZFRleHQoKHRleHQpID0+IHtcclxuXHRcdFx0XHRcdG5ldyBGaWxlU3VnZ2VzdCh0aGlzLmFwcCwgdGV4dC5pbnB1dEVsKVxyXG5cdFx0XHRcdFx0dGV4dFxyXG5cdFx0XHRcdFx0XHQuc2V0UGxhY2Vob2xkZXIoXCJQYXRoXCIpXHJcblx0XHRcdFx0XHRcdC5zZXRWYWx1ZShub3RlLnBhdGgpXHJcblx0XHRcdFx0XHRcdC5vbkNoYW5nZShhc3luYyAodmFsdWUpID0+IHtcclxuXHRcdFx0XHRcdFx0XHRjaGFuZ2VkUGF0aCA9IHZhbHVlO1xyXG5cdFx0XHRcdFx0XHR9KVxyXG5cdFx0XHRcdFx0fVxyXG5cdFx0XHRcdClcclxuXHRcdFx0XHQuYWRkVGV4dCgodGV4dCkgPT4gdGV4dFxyXG5cdFx0XHRcdFx0LnNldFBsYWNlaG9sZGVyKFwiSWNvbihvcHRpb25hbClcIilcclxuXHRcdFx0XHRcdC5zZXRWYWx1ZShub3RlLmljb24pXHJcblx0XHRcdFx0XHQub25DaGFuZ2UoYXN5bmMgKHZhbHVlKSA9PiB7XHJcblx0XHRcdFx0XHRcdGNoYW5nZWRJY29uID0gdmFsdWU7XHJcblx0XHRcdFx0XHR9KVxyXG5cdFx0XHRcdClcclxuXHRcdFx0XHQuYWRkQnV0dG9uKChidXR0b24pID0+IGJ1dHRvbi5zZXRJY29uKFwic2F2ZVwiKS5vbkNsaWNrKFxyXG5cdFx0XHRcdFx0YXN5bmMgKCkgPT4ge1xyXG5cdFx0XHRcdFx0XHRpZiAoXHJcblx0XHRcdFx0XHRcdFx0KGNoYW5nZWRUaXRsZSA9PT0gdW5kZWZpbmVkIHx8IGNoYW5nZWRUaXRsZSA9PT0gbm90ZS50aXRsZSkgJiZcclxuXHRcdFx0XHRcdFx0XHQoY2hhbmdlZFBhdGggPT09IHVuZGVmaW5lZCB8fCBjaGFuZ2VkUGF0aCA9PT0gbm90ZS5wYXRoKSAmJlxyXG5cdFx0XHRcdFx0XHRcdChjaGFuZ2VkSWNvbiA9PT0gdW5kZWZpbmVkIHx8IGNoYW5nZWRJY29uID09PSBub3RlLmljb24pXHJcblx0XHRcdFx0XHRcdCkge1xyXG5cdFx0XHRcdFx0XHRcdG5ldyBOb3RpY2UoXCJQcm92aWRlIGFueSBkYXRhXCIpXHJcblx0XHRcdFx0XHRcdFx0cmV0dXJuO1xyXG5cdFx0XHRcdFx0XHR9XHJcblx0XHRcdFx0XHRcdGlmIChjaGFuZ2VkVGl0bGUgIT09IHVuZGVmaW5lZCkge1xyXG5cdFx0XHRcdFx0XHRcdGlmIChjaGFuZ2VkVGl0bGUubGVuZ3RoICE9PSAwKSB7XHJcblx0XHRcdFx0XHRcdFx0XHRub3RlLnRpdGxlID0gY2hhbmdlZFRpdGxlXHJcblx0XHRcdFx0XHRcdFx0XHRjaGFuZ2VkVGl0bGUgPSB1bmRlZmluZWRcclxuXHRcdFx0XHRcdFx0XHR9XHJcblx0XHRcdFx0XHRcdFx0ZWxzZSBuZXcgTm90aWNlKFwiUHJvdmlkZSB0aXRsZVwiKVxyXG5cdFx0XHRcdFx0XHR9XHJcblx0XHRcdFx0XHRcdGlmIChjaGFuZ2VkUGF0aCAhPT0gdW5kZWZpbmVkKSB7XHJcblx0XHRcdFx0XHRcdFx0aWYgKGNoYW5nZWRQYXRoLmxlbmd0aCAhPT0gMCkge1xyXG5cdFx0XHRcdFx0XHRcdFx0bm90ZS5wYXRoID0gY2hhbmdlZFBhdGhcclxuXHRcdFx0XHRcdFx0XHRcdGNoYW5nZWRQYXRoID0gdW5kZWZpbmVkXHJcblx0XHRcdFx0XHRcdFx0fVxyXG5cdFx0XHRcdFx0XHRcdGVsc2UgbmV3IE5vdGljZShcIlByb3ZpZGUgcGF0aFwiKVxyXG5cdFx0XHRcdFx0XHR9XHJcblx0XHRcdFx0XHRcdGlmIChjaGFuZ2VkSWNvbiAhPT0gdW5kZWZpbmVkKSB7XHJcblx0XHRcdFx0XHRcdFx0bm90ZS5pY29uID0gY2hhbmdlZEljb25cclxuXHRcdFx0XHRcdFx0XHRjaGFuZ2VkSWNvbiA9IHVuZGVmaW5lZFxyXG5cdFx0XHRcdFx0XHR9XHJcblxyXG5cdFx0XHRcdFx0XHRhd2FpdCB0aGlzLnBsdWdpbi5zYXZlU2V0dGluZ3MoKVxyXG5cdFx0XHRcdFx0XHRhd2FpdCB0aGlzLnBsdWdpbi5sb2FkU2V0dGluZ3MoKVxyXG5cdFx0XHRcdFx0XHR0aGlzLmRpc3BsYXkoKVxyXG5cdFx0XHRcdFx0fSlcclxuXHRcdFx0XHQpXHJcblx0XHRcdFx0LmFkZEJ1dHRvbigoYnV0dG9uKSA9PiBidXR0b24uc2V0SWNvbihcInRyYXNoLTJcIikuc2V0V2FybmluZygpLm9uQ2xpY2soXHJcblx0XHRcdFx0XHRhc3luYyAoKSA9PiB7XHJcblx0XHRcdFx0XHRcdGF3YWl0IHRoaXMucGx1Z2luLnJlbW92ZVBpbm5lZE5vdGUobm90ZS5pZCk7XHJcblx0XHRcdFx0XHRcdHRoaXMuZGlzcGxheSgpXHJcblx0XHRcdFx0XHR9XHJcblx0XHRcdFx0KSlcclxuXHRcdH0pXHJcblx0fVxyXG59XHJcblxyXG5leHBvcnQgY2xhc3MgRmlsZVN1Z2dlc3QgZXh0ZW5kcyBBYnN0cmFjdElucHV0U3VnZ2VzdDxURmlsZT4ge1xyXG5cdHRleHRJbnB1dEVsOiBIVE1MSW5wdXRFbGVtZW50O1xyXG5cclxuXHRnZXRTdWdnZXN0aW9ucyhpbnB1dFN0cjogc3RyaW5nKTogVEZpbGVbXSB7XHJcblx0XHRjb25zdCBhYnN0cmFjdEZpbGVzID0gdGhpcy5hcHAudmF1bHQuZ2V0QWxsTG9hZGVkRmlsZXMoKTtcclxuXHRcdGNvbnN0IGZpbGVzOiBURmlsZVtdID0gW107XHJcblx0XHRjb25zdCBpbnB1dExvd2VyID0gaW5wdXRTdHIudG9Mb3dlckNhc2UoKTtcclxuXHJcblx0XHRhYnN0cmFjdEZpbGVzLmZvckVhY2goKGZpbGU6IFRBYnN0cmFjdEZpbGUpID0+IHtcclxuXHRcdFx0aWYgKFxyXG5cdFx0XHRcdGZpbGUgaW5zdGFuY2VvZiBURmlsZSAmJiBbXCJtZFwiLCBcImNhbnZhc1wiXS5jb250YWlucyhmaWxlLmV4dGVuc2lvbikgJiZcclxuXHRcdFx0XHRmaWxlLnBhdGgudG9Mb3dlckNhc2UoKS5jb250YWlucyhpbnB1dExvd2VyKVxyXG5cdFx0XHQpIHtcclxuXHRcdFx0XHRmaWxlcy5wdXNoKGZpbGUpO1xyXG5cdFx0XHR9XHJcblx0XHR9KTtcclxuXHRcdHJldHVybiBmaWxlcztcclxuXHR9XHJcblxyXG5cdHJlbmRlclN1Z2dlc3Rpb24oZmlsZTogVEZpbGUsIGVsOiBIVE1MRWxlbWVudCkge1xyXG5cdFx0aWYgKGZpbGUuZXh0ZW5zaW9uID09IFwibWRcIikge1xyXG5cdFx0XHRlbC5zZXRUZXh0KHRyaW1GaWxlKGZpbGUpKTtcclxuXHRcdH1cclxuXHRcdGVsc2Uge1xyXG5cdFx0XHQvL3dlIGRvbid0IHVzZSB0cmltRmlsZSBoZXJlIGFzIHRoZSBleHRlbnNpb24gaXNuJ3QgZGlzcGxheWVkIGhlcmVcclxuXHRcdFx0ZWwuc2V0VGV4dChmaWxlLnBhdGguc2xpY2UoMCwgLTcpKVxyXG5cdFx0XHRlbC5pbnNlcnRBZGphY2VudEhUTUwoXHJcblx0XHRcdFx0XCJiZWZvcmVlbmRcIixcclxuXHRcdFx0XHRgPGRpdiBjbGFzcz1cIm5hdi1maWxlLXRhZ1wiIHN0eWxlPVwiZGlzcGxheTppbmxpbmUtYmxvY2s7dmVydGljYWwtYWxpZ246bWlkZGxlXCI+Y2FudmFzPC9kaXY+YFxyXG5cdFx0XHQpO1xyXG5cdFx0fVxyXG5cdH1cclxuXHJcblx0c2VsZWN0U3VnZ2VzdGlvbihmaWxlOiBURmlsZSkge1xyXG5cdFx0dGhpcy50ZXh0SW5wdXRFbC52YWx1ZSA9IHRyaW1GaWxlKGZpbGUpO1xyXG5cdFx0dGhpcy50ZXh0SW5wdXRFbC50cmlnZ2VyKFwiaW5wdXRcIik7XHJcblx0XHR0aGlzLmNsb3NlKCk7XHJcblx0fVxyXG59XHJcblxyXG5leHBvcnQgZnVuY3Rpb24gdHJpbUZpbGUoZmlsZTogVEZpbGUpOiBzdHJpbmcge1xyXG5cdGlmICghZmlsZSkgcmV0dXJuIFwiXCI7XHJcblx0cmV0dXJuIGZpbGUuZXh0ZW5zaW9uID09IFwibWRcIiA/IGZpbGUucGF0aC5zbGljZSgwLCAtMyk6IGZpbGUucGF0aDtcclxufVxyXG4iLCAiLy8gVW5pcXVlIElEIGNyZWF0aW9uIHJlcXVpcmVzIGEgaGlnaCBxdWFsaXR5IHJhbmRvbSAjIGdlbmVyYXRvci4gSW4gdGhlIGJyb3dzZXIgd2UgdGhlcmVmb3JlXG4vLyByZXF1aXJlIHRoZSBjcnlwdG8gQVBJIGFuZCBkbyBub3Qgc3VwcG9ydCBidWlsdC1pbiBmYWxsYmFjayB0byBsb3dlciBxdWFsaXR5IHJhbmRvbSBudW1iZXJcbi8vIGdlbmVyYXRvcnMgKGxpa2UgTWF0aC5yYW5kb20oKSkuXG5sZXQgZ2V0UmFuZG9tVmFsdWVzO1xuY29uc3Qgcm5kczggPSBuZXcgVWludDhBcnJheSgxNik7XG5leHBvcnQgZGVmYXVsdCBmdW5jdGlvbiBybmcoKSB7XG4gIC8vIGxhenkgbG9hZCBzbyB0aGF0IGVudmlyb25tZW50cyB0aGF0IG5lZWQgdG8gcG9seWZpbGwgaGF2ZSBhIGNoYW5jZSB0byBkbyBzb1xuICBpZiAoIWdldFJhbmRvbVZhbHVlcykge1xuICAgIC8vIGdldFJhbmRvbVZhbHVlcyBuZWVkcyB0byBiZSBpbnZva2VkIGluIGEgY29udGV4dCB3aGVyZSBcInRoaXNcIiBpcyBhIENyeXB0byBpbXBsZW1lbnRhdGlvbi5cbiAgICBnZXRSYW5kb21WYWx1ZXMgPSB0eXBlb2YgY3J5cHRvICE9PSAndW5kZWZpbmVkJyAmJiBjcnlwdG8uZ2V0UmFuZG9tVmFsdWVzICYmIGNyeXB0by5nZXRSYW5kb21WYWx1ZXMuYmluZChjcnlwdG8pO1xuXG4gICAgaWYgKCFnZXRSYW5kb21WYWx1ZXMpIHtcbiAgICAgIHRocm93IG5ldyBFcnJvcignY3J5cHRvLmdldFJhbmRvbVZhbHVlcygpIG5vdCBzdXBwb3J0ZWQuIFNlZSBodHRwczovL2dpdGh1Yi5jb20vdXVpZGpzL3V1aWQjZ2V0cmFuZG9tdmFsdWVzLW5vdC1zdXBwb3J0ZWQnKTtcbiAgICB9XG4gIH1cblxuICByZXR1cm4gZ2V0UmFuZG9tVmFsdWVzKHJuZHM4KTtcbn0iLCAiaW1wb3J0IHZhbGlkYXRlIGZyb20gJy4vdmFsaWRhdGUuanMnO1xuLyoqXG4gKiBDb252ZXJ0IGFycmF5IG9mIDE2IGJ5dGUgdmFsdWVzIHRvIFVVSUQgc3RyaW5nIGZvcm1hdCBvZiB0aGUgZm9ybTpcbiAqIFhYWFhYWFhYLVhYWFgtWFhYWC1YWFhYLVhYWFhYWFhYWFhYWFxuICovXG5cbmNvbnN0IGJ5dGVUb0hleCA9IFtdO1xuXG5mb3IgKGxldCBpID0gMDsgaSA8IDI1NjsgKytpKSB7XG4gIGJ5dGVUb0hleC5wdXNoKChpICsgMHgxMDApLnRvU3RyaW5nKDE2KS5zbGljZSgxKSk7XG59XG5cbmV4cG9ydCBmdW5jdGlvbiB1bnNhZmVTdHJpbmdpZnkoYXJyLCBvZmZzZXQgPSAwKSB7XG4gIC8vIE5vdGU6IEJlIGNhcmVmdWwgZWRpdGluZyB0aGlzIGNvZGUhICBJdCdzIGJlZW4gdHVuZWQgZm9yIHBlcmZvcm1hbmNlXG4gIC8vIGFuZCB3b3JrcyBpbiB3YXlzIHlvdSBtYXkgbm90IGV4cGVjdC4gU2VlIGh0dHBzOi8vZ2l0aHViLmNvbS91dWlkanMvdXVpZC9wdWxsLzQzNFxuICByZXR1cm4gYnl0ZVRvSGV4W2FycltvZmZzZXQgKyAwXV0gKyBieXRlVG9IZXhbYXJyW29mZnNldCArIDFdXSArIGJ5dGVUb0hleFthcnJbb2Zmc2V0ICsgMl1dICsgYnl0ZVRvSGV4W2FycltvZmZzZXQgKyAzXV0gKyAnLScgKyBieXRlVG9IZXhbYXJyW29mZnNldCArIDRdXSArIGJ5dGVUb0hleFthcnJbb2Zmc2V0ICsgNV1dICsgJy0nICsgYnl0ZVRvSGV4W2FycltvZmZzZXQgKyA2XV0gKyBieXRlVG9IZXhbYXJyW29mZnNldCArIDddXSArICctJyArIGJ5dGVUb0hleFthcnJbb2Zmc2V0ICsgOF1dICsgYnl0ZVRvSGV4W2FycltvZmZzZXQgKyA5XV0gKyAnLScgKyBieXRlVG9IZXhbYXJyW29mZnNldCArIDEwXV0gKyBieXRlVG9IZXhbYXJyW29mZnNldCArIDExXV0gKyBieXRlVG9IZXhbYXJyW29mZnNldCArIDEyXV0gKyBieXRlVG9IZXhbYXJyW29mZnNldCArIDEzXV0gKyBieXRlVG9IZXhbYXJyW29mZnNldCArIDE0XV0gKyBieXRlVG9IZXhbYXJyW29mZnNldCArIDE1XV07XG59XG5cbmZ1bmN0aW9uIHN0cmluZ2lmeShhcnIsIG9mZnNldCA9IDApIHtcbiAgY29uc3QgdXVpZCA9IHVuc2FmZVN0cmluZ2lmeShhcnIsIG9mZnNldCk7IC8vIENvbnNpc3RlbmN5IGNoZWNrIGZvciB2YWxpZCBVVUlELiAgSWYgdGhpcyB0aHJvd3MsIGl0J3MgbGlrZWx5IGR1ZSB0byBvbmVcbiAgLy8gb2YgdGhlIGZvbGxvd2luZzpcbiAgLy8gLSBPbmUgb3IgbW9yZSBpbnB1dCBhcnJheSB2YWx1ZXMgZG9uJ3QgbWFwIHRvIGEgaGV4IG9jdGV0IChsZWFkaW5nIHRvXG4gIC8vIFwidW5kZWZpbmVkXCIgaW4gdGhlIHV1aWQpXG4gIC8vIC0gSW52YWxpZCBpbnB1dCB2YWx1ZXMgZm9yIHRoZSBSRkMgYHZlcnNpb25gIG9yIGB2YXJpYW50YCBmaWVsZHNcblxuICBpZiAoIXZhbGlkYXRlKHV1aWQpKSB7XG4gICAgdGhyb3cgVHlwZUVycm9yKCdTdHJpbmdpZmllZCBVVUlEIGlzIGludmFsaWQnKTtcbiAgfVxuXG4gIHJldHVybiB1dWlkO1xufVxuXG5leHBvcnQgZGVmYXVsdCBzdHJpbmdpZnk7IiwgImNvbnN0IHJhbmRvbVVVSUQgPSB0eXBlb2YgY3J5cHRvICE9PSAndW5kZWZpbmVkJyAmJiBjcnlwdG8ucmFuZG9tVVVJRCAmJiBjcnlwdG8ucmFuZG9tVVVJRC5iaW5kKGNyeXB0byk7XG5leHBvcnQgZGVmYXVsdCB7XG4gIHJhbmRvbVVVSURcbn07IiwgImltcG9ydCBuYXRpdmUgZnJvbSAnLi9uYXRpdmUuanMnO1xuaW1wb3J0IHJuZyBmcm9tICcuL3JuZy5qcyc7XG5pbXBvcnQgeyB1bnNhZmVTdHJpbmdpZnkgfSBmcm9tICcuL3N0cmluZ2lmeS5qcyc7XG5cbmZ1bmN0aW9uIHY0KG9wdGlvbnMsIGJ1Ziwgb2Zmc2V0KSB7XG4gIGlmIChuYXRpdmUucmFuZG9tVVVJRCAmJiAhYnVmICYmICFvcHRpb25zKSB7XG4gICAgcmV0dXJuIG5hdGl2ZS5yYW5kb21VVUlEKCk7XG4gIH1cblxuICBvcHRpb25zID0gb3B0aW9ucyB8fCB7fTtcbiAgY29uc3Qgcm5kcyA9IG9wdGlvbnMucmFuZG9tIHx8IChvcHRpb25zLnJuZyB8fCBybmcpKCk7IC8vIFBlciA0LjQsIHNldCBiaXRzIGZvciB2ZXJzaW9uIGFuZCBgY2xvY2tfc2VxX2hpX2FuZF9yZXNlcnZlZGBcblxuICBybmRzWzZdID0gcm5kc1s2XSAmIDB4MGYgfCAweDQwO1xuICBybmRzWzhdID0gcm5kc1s4XSAmIDB4M2YgfCAweDgwOyAvLyBDb3B5IGJ5dGVzIHRvIGJ1ZmZlciwgaWYgcHJvdmlkZWRcblxuICBpZiAoYnVmKSB7XG4gICAgb2Zmc2V0ID0gb2Zmc2V0IHx8IDA7XG5cbiAgICBmb3IgKGxldCBpID0gMDsgaSA8IDE2OyArK2kpIHtcbiAgICAgIGJ1ZltvZmZzZXQgKyBpXSA9IHJuZHNbaV07XG4gICAgfVxuXG4gICAgcmV0dXJuIGJ1ZjtcbiAgfVxuXG4gIHJldHVybiB1bnNhZmVTdHJpbmdpZnkocm5kcyk7XG59XG5cbmV4cG9ydCBkZWZhdWx0IHY0OyJdLAogICJtYXBwaW5ncyI6ICI7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7OztBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUEsc0JBV087OztBQ1JQLElBQUk7QUFDSixJQUFNLFFBQVEsSUFBSSxXQUFXLEVBQUU7QUFDaEIsU0FBUixNQUF1QjtBQUU1QixNQUFJLENBQUMsaUJBQWlCO0FBRXBCLHNCQUFrQixPQUFPLFdBQVcsZUFBZSxPQUFPLG1CQUFtQixPQUFPLGdCQUFnQixLQUFLLE1BQU07QUFFL0csUUFBSSxDQUFDLGlCQUFpQjtBQUNwQixZQUFNLElBQUksTUFBTSwwR0FBMEc7QUFBQSxJQUM1SDtBQUFBLEVBQ0Y7QUFFQSxTQUFPLGdCQUFnQixLQUFLO0FBQzlCOzs7QUNYQSxJQUFNLFlBQVksQ0FBQztBQUVuQixTQUFTLElBQUksR0FBRyxJQUFJLEtBQUssRUFBRSxHQUFHO0FBQzVCLFlBQVUsTUFBTSxJQUFJLEtBQU8sU0FBUyxFQUFFLEVBQUUsTUFBTSxDQUFDLENBQUM7QUFDbEQ7QUFFTyxTQUFTLGdCQUFnQixLQUFLLFNBQVMsR0FBRztBQUcvQyxTQUFPLFVBQVUsSUFBSSxTQUFTLENBQUMsQ0FBQyxJQUFJLFVBQVUsSUFBSSxTQUFTLENBQUMsQ0FBQyxJQUFJLFVBQVUsSUFBSSxTQUFTLENBQUMsQ0FBQyxJQUFJLFVBQVUsSUFBSSxTQUFTLENBQUMsQ0FBQyxJQUFJLE1BQU0sVUFBVSxJQUFJLFNBQVMs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
