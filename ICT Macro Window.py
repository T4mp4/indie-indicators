# indie:lang_version = 5
from math import nan
from indie import indicator, param, color, plot, MainContext, Optional, Var
from indie.drawings import Rectangle, AbsolutePosition


@indicator('ICT Macro Window', overlay_main_pane=True)
@param.int('window_start_min', default=50, min=0, max=59, title='Macro Starts')
@param.int('window_end_min', default=10, min=0, max=59, title='Macro Ends')
@param.color('line_color', default=color.PURPLE, title='Macro Opening Price Color')
@param.color('box_color', default=color.PURPLE(0.30), title='Macro Window Color')
@param.color('border_color', default=color.BLACK(0.01), title='Border Color')
@param.int('border_width', default=0, min=0, max=5, title='Border Width')

@plot.line(title='Window Open Price')
class Main(MainContext):
    def calc(self, window_start_min, window_end_min, box_color, border_color, border_width, line_color):
        prev_in_window = Var[bool].new(False)
        window_open_price = Var[float].new(nan)
        window_high = Var[float].new(nan)
        window_low = Var[float].new(nan)
        window_start_time = Var[float].new(nan)
        window_box = Var[Optional[Rectangle]].new(None)

        in_window = False
        is_window_start = False

        if self.time_frame.to_minutes() <= 5:
            minute = (int(self.time[0]) % 3600) // 60
            if window_start_min <= window_end_min:
                in_window = minute >= window_start_min and minute <= window_end_min
            else:
                in_window = minute >= window_start_min or minute <= window_end_min
            is_window_start = in_window and not prev_in_window.get()

        window_ended = prev_in_window.get() and not in_window

        if is_window_start:
            window_open_price.set(self.open[0])
            window_high.set(self.high[0])
            window_low.set(self.low[0])
            window_start_time.set(self.time[0])
            window_box.set(Rectangle(
                AbsolutePosition(self.time[0], self.high[0]),
                AbsolutePosition(self.time[0], self.low[0]),
                line_width=border_width,
                line_color=border_color,
                bg_color=box_color,
            ))
        elif in_window:
            if self.high[0] > window_high.get():
                window_high.set(self.high[0])
            if self.low[0] < window_low.get():
                window_low.set(self.low[0])
            if window_box.get() is not None:
                active_box = window_box.get().value()
                active_box.point_a = AbsolutePosition(window_start_time.get(), window_high.get())
                active_box.point_b = AbsolutePosition(self.time[0], window_low.get())

        # Grow the live window's box in place; draw a completed historical box once when it closes.
        if window_box.get() is not None:
            if in_window:
                if self.is_realtime or self.is_last_bar:
                    self.chart.draw(window_box.get().value())
            elif window_ended:
                self.chart.draw(window_box.get().value())

        line_value = nan
        if in_window:
            line_value = window_open_price.get()

        prev_in_window.set(in_window)

        return plot.Line(line_value, color=line_color)
