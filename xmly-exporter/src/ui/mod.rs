mod event_loop;

pub fn display() {
    // --- external ---
    use conrod::backend::glium::glium::{self, Surface, glutin};
    // --- custom ---
    use crate::fetcher::album::Album;
    use self::event_loop::EventLoop;

    const WIDTH: u32 = 1000;
    const HEIGHT: u32 = 300;

    let mut events_loop = glutin::EventsLoop::new();
    let window_builder = glutin::WindowBuilder::new()
        .with_title("xmly-exporter")
        .with_dimensions((WIDTH, HEIGHT).into());
    let context_builder = glutin::ContextBuilder::new()
        .with_vsync(true)
        .with_multisampling(4);
    let display = glium::Display::new(window_builder, context_builder, &events_loop).unwrap();

    let mut ui = conrod::UiBuilder::new([WIDTH as f64, HEIGHT as f64]).build();

    {
        // --- std ---
        use std::path::Path;

        if cfg!(target_os = "windows") {
            ui.fonts.insert_from_file(Path::new("C:/Windows/Fonts/simsunb.ttf")).unwrap();
        } else {
            ui.fonts.insert_from_file(Path::new("/Library/Fonts/Arial Unicode.ttf")).unwrap();
        };
    }

    widget_ids! { struct Ids {
        canvas,
        get_album_detail_button,
        download_album_button,
        album_id_text_box,
        track_list_select,
    } }
    let ids = Ids::new(ui.widget_id_generator());

    let image_map = conrod::image::Map::<glium::texture::Texture2d>::new();
    let mut renderer = conrod::backend::glium::Renderer::new(&display).unwrap();

    let mut album = Album::new();
    let mut album_id = String::new();
    let mut tracks = vec![];
    let mut track_selected = std::collections::HashSet::new();

    let mut event_loop = EventLoop::new();
    'main: loop {
        for event in event_loop.next(&mut events_loop) {
            if let Some(event) = conrod::backend::winit::convert_event(event.clone(), &display) {
                ui.handle_event(event);
                event_loop.needs_update();
            }

            match event {
                glutin::Event::WindowEvent { event, .. } => match event {
                    glutin::WindowEvent::KeyboardInput {
                        input: glutin::KeyboardInput {
                            virtual_keycode: Some(glutin::VirtualKeyCode::Escape),
                            ..
                        },
                        ..
                    } => break 'main,
                    _ => ()
                }
                _ => ()
            }
        }

        {
            // --- external ---
            use conrod::{Borderable, Colorable, Labelable, Positionable, Sizeable, Widget, color, widget};

            let ui = &mut ui.set_widgets();

            widget::Canvas::new()
                .color(color::DARK_CHARCOAL)
                .set(ids.canvas, ui);

            let widget_width = 80.;
            let widget_height = 30.;
            let font_size = 15. as conrod::FontSize;

            {
                for edit in widget::TextBox::new(&album_id)
                    .w_h(widget_width, widget_height)
                    .font_size(font_size)
                    .color(color::WHITE)
                    .top_left_with_margins_on(ids.canvas, 40., 40.)
                    .center_justify()
                    .set(ids.album_id_text_box, ui) {
                    if let conrod::widget::text_box::Event::Update(s) = edit { album_id = s; }
                }
            }

            {
                let button_color = color::LIGHT_BLUE;
                let button_press_color = color::LIGHT_GREY;
                let label_color = color::BLACK;

                if widget::Button::new()
                    .label("Detail")
                    .w_h(widget_width, widget_height)
                    .label_font_size(font_size)
                    .mid_top_with_margin_on(ids.album_id_text_box, 40.)
                    .border(0.)
                    .color(button_color)
                    .label_color(label_color)
                    .press_color(button_press_color)
                    .set(ids.get_album_detail_button, ui)
                    .was_clicked() {
                    tracks = album
                        .set_id(&album_id)
                        .fetch()
                        .tracks_detail();
                }

                if widget::Button::new()
                    .label("Export")
                    .w_h(widget_width, widget_height)
                    .label_font_size(font_size)
                    .mid_top_with_margin_on(ids.get_album_detail_button, 40.)
                    .border(0.)
                    .color(button_color)
                    .label_color(label_color)
                    .press_color(button_press_color)
                    .set(ids.download_album_button, ui)
                    .was_clicked() {
                    album.save_aria2_input_file();
                }
            }

            {
                let tracks_amount = tracks.len();
                let (mut events, scrollbar) = widget::ListSelect::multiple(tracks_amount)
                    .flow_down()
                    .item_size(widget_height)
                    .scrollbar_color(color::WHITE)
                    .scrollbar_next_to()
                    .w_h(800., 230.)
                    .top_right_with_margins_on(ids.canvas, 40., 40.)
                    .set(ids.track_list_select, ui);

                while let Some(event) = events.next(ui, |i| track_selected.contains(&i)) {
                    // --- external ---
                    use conrod::widget::list_select::Event;

                    match event {
                        Event::Item(item) => {
                            let label = &tracks[item.i];
                            let (color, label_color) = match track_selected.contains(&item.i) {
                                true => (color::LIGHT_BLUE, color::YELLOW),
                                false => (color::LIGHT_GREY, color::BLACK),
                            };
                            let button = widget::Button::new()
                                .border(0.)
                                .color(color)
                                .label(label)
                                .label_font_size(font_size)
                                .label_color(label_color);
                            item.set(button, ui);
                        }
                        Event::Selection(selection) => {
                            selection.update_index_set(&mut track_selected);
//                        println!("selected indices: {:?}", track_selected);
                        }
                        _event => {
                            ()
//                        println!("{:?}", &_event)
                        }
                    }
                }

                if let Some(s) = scrollbar { s.set(ui); }
            }
        }

        if let Some(primitives) = ui.draw_if_changed() {
            renderer.fill(&display, primitives, &image_map);
            let mut target = display.draw();
            target.clear_color(0., 0., 0., 1.);
            renderer.draw(&display, &mut target, &image_map).unwrap();
            target.finish().unwrap();
        }
    }
}
