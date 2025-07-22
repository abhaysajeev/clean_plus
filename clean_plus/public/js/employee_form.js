frappe.ui.form.on('Employee', {
    refresh(frm) {
        // Attach popup buttons to Malayalam fields
        bind_field_popup(frm, 'custom_first_name_malayalam', 'first_name');
        bind_field_popup(frm, 'custom_last_name_malayalam', 'last_name');
        bind_field_popup(frm, 'custom_malayalam_translator', 'custom_malayalam_converter');
    },

    before_save(frm) {
        const first_name_malayalam = frm.doc.custom_first_name_malayalam || '';
        const last_name_malayalam = frm.doc.custom_last_name_malayalam || '';

        const full_name_malayalam = [first_name_malayalam, last_name_malayalam]
            .filter(Boolean)
            .join(' ')
            .trim();

        frm.set_value('custom_full_name_malayalam', full_name_malayalam);
    },

    custom_malayalam_converter(frm) {
        // Auto-transliterate on typing
        translate_name(frm, false, 'custom_malayalam_converter', 'custom_malayalam_translator');
    },

    first_name(frm) {
        translate_name(frm, false, 'first_name', 'custom_first_name_malayalam');
    },

    last_name(frm) {
        translate_name(frm, false, 'last_name', 'custom_last_name_malayalam');
    }
});


// Add popup icon/button inside field
function bind_field_popup(frm, mal_fieldname, source_fieldname) {
    const field = frm.get_field(mal_fieldname);
    if (!field) return;

    if (field.$wrapper.find('.popup-trigger-btn').length) return;

    const $inputGroup = $('<div class="input-group"></div>');
    const $iconBtn = $(`
        <span class="input-group-text popup-trigger-btn" title="Choose transliteration" style="cursor: pointer;font-size: 12px; padding: 2px 4px; ">
            🌐
        </span>
    `);

    $iconBtn.on('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        show_popup_above(field.$input, frm, mal_fieldname, source_fieldname);
    });

    field.$input.wrap($inputGroup);
    field.$input.parent().append($iconBtn);
}


// Show popup with transliteration suggestions
function show_popup_above($field_input, frm, mal_fieldname, source_fieldname) {
    const source_val = frm.doc[source_fieldname]?.trim();
    if (!source_val) return;

    $('.field-popup-dialog').remove();

    const offset = $field_input.offset();
    const html = `
        <div class="field-popup-dialog" style="
            position: absolute;
            z-index: 2000;
            background: white;
            border: 1px solid #d1d8dd;
            border-radius: 12px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
            padding: 8px;
            width: 180px;
            left: ${offset.left}px;
            top: ${offset.top - 100}px;
        ">
            <div style="
                position: absolute;
                bottom: -8px;
                left: 20px;
                width: 0; height: 0;
                border-left: 8px solid transparent;
                border-right: 8px solid transparent;
                border-top: 8px solid #d1d8dd;
            "></div>
            <div style="
                position: absolute;
                bottom: -7px;
                left: 21px;
                width: 0; height: 0;
                border-left: 7px solid transparent;
                border-right: 7px solid transparent;
                border-top: 7px solid white;
            "></div>
            <div id="buttonContainer"></div>
        </div>
    `;

    $('body').append(html);

    // Fetch and show transliteration options
    translate_name(frm, true, source_fieldname, mal_fieldname);

    // Close popup on outside click or Escape key
    $(document).on('click.popup', function (e) {
        if (!$(e.target).closest('.field-popup-dialog, .frappe-control[data-fieldname="' + mal_fieldname + '"]').length) {
            $('.field-popup-dialog').remove();
            $(document).off('click.popup');
        }
    });

    $(document).on('keydown.popup', function (e) {
        if (e.key === "Escape") {
            $('.field-popup-dialog').remove();
            $(document).off('keydown.popup');
        }
    });
}


// Call server to get transliterated name & suggestions
function translate_name(frm, triggered_by_field_click = false, source_fieldname, target_fieldname = '') {
    const name = frm.doc[source_fieldname]?.trim();
    if (!name) {
        $('.field-popup-dialog').remove();
        return;
    }

    frappe.call({
        method: "clean_plus.services.name_translation.transliterate_name",
        args: { name },
        callback: function(response) {
            if (!response.message) return;

            const transliterated = response.message.transliterated || '';
            const candidates = response.message.candidates || [];

            if (!triggered_by_field_click) {
                // Auto-fill
                const auto_target_field = target_fieldname ||
                    (source_fieldname === 'first_name' ? 'custom_first_name_malayalam' : 'custom_last_name_malayalam');
                frm.set_value(auto_target_field, transliterated);
                return;
            }

            if (triggered_by_field_click && target_fieldname) {
                const options = [...new Set([transliterated, ...candidates])];
                const $container = $('#buttonContainer');
                $container.empty();

                options.forEach(option => {
                    const $btn = $(`<button class="btn btn-sm popup-btn" style="width:100%; margin-bottom:4px;">${option}</button>`);
                    $btn.on('click', function () {
                        frm.set_value(target_fieldname, option);
                        frm.refresh_field(target_fieldname);
                        $('.field-popup-dialog').remove();
                        $(document).off('click.popup');
                        $(document).off('keydown.popup');
                    });
                    $container.append($btn);
                });
            }
        }
    });
}
