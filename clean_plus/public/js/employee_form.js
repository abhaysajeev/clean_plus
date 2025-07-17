frappe.ui.form.on('Employee', {
  refresh(frm) {
    bind_field_popup(frm, 'custom_full_name_malayalam');
  },
first_name: function(frm) {
    translate_name(frm);
},
middle_name: function(frm) {
    translate_name(frm);
},
last_name: function(frm) {
    translate_name(frm);
}
});

function bind_field_popup(frm, fieldname) {
    const field = frm.get_field(fieldname);
    if (!field) return;

    field.$input
        .css('cursor', 'pointer')
        .off('click.field_popup')
        .on('click.field_popup', function (e) {
            e.preventDefault();
            show_popup_above(field.$input, frm, fieldname);
        });
}

function show_popup_above($field_input, frm, fieldname) {
    // Check if full name is empty BEFORE rendering the popup
    const full_name = [frm.doc.first_name, frm.doc.middle_name, frm.doc.last_name]
        .filter(Boolean).join(' ').trim();

    if (!full_name) return; // Do nothing if name is empty

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

    // Now populate buttons based on API result
    translate_name(frm, true, fieldname);

    // Dismiss popup
    $(document).on('click.popup', function (e) {
        if (!$(e.target).closest('.field-popup-dialog, .frappe-control[data-fieldname="' + fieldname + '"]').length) {
            $('.field-popup-dialog').remove();
            $(document).off('click.popup');
        }
    });

    $(document).on('keydown.popup', function (e) {
        if (e.key === "Escape") {
            $('.field-popup-dialog').remove();
            $(document).off('click.popup');
        }
    });
}

function translate_name(frm, triggered_by_field_click = false, fieldname = '') {
    let full_name = '';

    if (frm.doc.first_name) full_name += frm.doc.first_name;
    if (frm.doc.middle_name) full_name += ' ' + frm.doc.middle_name;
    if (frm.doc.last_name) full_name += ' ' + frm.doc.last_name;

    full_name = full_name.trim();

    if (!full_name) {
        // No popup if name is empty
        $('.field-popup-dialog').remove();
        return;
    }

    frappe.call({
        method: "clean_plus.services.name_translation.transliterate_name",
        args: { name: full_name },
        callback: function(response) {
            if (!response.message) return;

            const transliterated = response.message.transliterated || '';
            const candidates = response.message.candidates || [];

            if (!triggered_by_field_click) {
                // Auto-fill field if triggered by typing
                frm.set_value('custom_full_name_malayalam', transliterated);
            }

            if (triggered_by_field_click && fieldname) {
                let options = [...candidates];

                // Ensure main transliteration is included
                if (!options.includes(transliterated)) {
                    options.unshift(transliterated);
                }

                const $container = $('#buttonContainer');
                $container.empty(); // Clear previous buttons

                options.forEach(option => {
                    const $btn = $(`<button class="btn btn-sm popup-btn" style="width:100%; margin-bottom:4px;">${option}</button>`);
                    $btn.attr('data-val', option);
                    $btn.on('click', function () {
                        frm.set_value(fieldname, option);
                        frm.refresh_field(fieldname);
                        $('.field-popup-dialog').remove();
                    });
                    $container.append($btn);
                });
            }
        }
    });
}

