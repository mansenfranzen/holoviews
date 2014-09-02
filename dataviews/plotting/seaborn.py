from __future__ import absolute_import

import matplotlib.pyplot as plt

try:
    import seaborn.apionly as sns
except:
    sns = None

import param

from ..dataviews import DataStack
from ..interface.seaborn import Regression, TimeSeries, SNSFrame,\
    Bivariate, Distribution
from ..views import View
from .viewplots import Plot
from .pandas import DFrameViewPlot


class SeabornPlot(Plot):
    """
    Seaborn Plot provides an abstract baseclass, defining how
    Seaborn based plots are updated.
    """

    rescale_individually = param.Boolean(default=False, doc="""
        Whether to use redraw the axes per stack or per view.""")

    _abstract = True

    def update_frame(self, n, lbrt=None):
        n = n if n < len(self) else len(self) - 1
        view = list(self._stack.values())[n]
        if lbrt is None:
            lbrt = view.lbrt if self.rescale_individually else self._stack.lbrt
        if self.zorder == 0 and self.ax: self.ax.cla()
        self._axis(self.ax, self._format_title(n), view.xlabel,
                   view.ylabel, lbrt=lbrt)
        self._update_plot(n)
        plt.draw()



class RegressionPlot(SeabornPlot):
    """
    RegressionPlot visualizes Regression Views using the seaborn
    regplot interface, allowing the user to perform and plot
    linear regressions on a set of scatter points. Parameters
    to the replot function can be supplied via the opts magic.
    """

    style_opts = param.List(default=['x_estimator', 'x_bins', 'x_ci',
                                     'scatter', 'fit_reg', 'color',
                                     'n_boot', 'order', 'logistic',
                                     'lowess', 'robust', 'truncate',
                                     'scatter_kws', 'line_kws', 'ci',
                                     'dropna', 'x_jitter', 'y_jitter',
                                     'x_partial', 'y_partial'],
                            constant=True, doc="""
       The style options for CurvePlot match those of matplotlib's
       LineCollection object.""")

    _stack_type = DataStack
    _view_type = Regression

    def __call__(self, axis=None, cyclic_index=0, lbrt=None):
        scatterview = self._stack.last
        self.cyclic_index = cyclic_index

        if lbrt is None:
            lbrt = scatterview.lbrt if self.rescale_individually else self._stack.lbrt

        self.ax = self._axis(axis, self._format_title(-1), scatterview.xlabel,
                             scatterview.ylabel, lbrt=lbrt)

        self._update_plot(-1)

        if axis is None: plt.close(self.handles['fig'])
        return self.ax if axis else self.handles['fig']

    def _update_plot(self, n):
        n = n if n < len(self) else len(self) - 1
        scatterview = list(self._stack.values())[n]
        sns.regplot(scatterview.data[:, 0], scatterview.data[:, 1],
                    ax=self.ax, label=scatterview.legend_label,
                    **View.options.style(scatterview)[self.cyclic_index])



class BivariatePlot(SeabornPlot):
    """
    Bivariate plot visualizes two-dimensional kernel density
    estimates using the Seaborn kdeplot function. Additionally,
    by enabling the joint option, the marginals distributions
    can be plotted alongside each axis (does not animate or
    compose).
    """

    rescale_individually = param.Boolean(default=True)

    joint = param.Boolean(default=False, doc="""
        Whether to visualize the kernel density estimate with marginal
        distributions along each axis. Does not animate or compose
        when enabled.""")

    style_opts = param.List(default=['color', 'alpha', 'err_style',
                                     'interpolate', 'ci', 'kind',
                                     'bw', 'kernel', 'cumulative',
                                     'shade', 'vertical', 'cmap'],
                            constant=True, doc="""
       The style options for BivariatePlot match those of seaborns
       kdeplot.""")

    _stack_type = DataStack
    _view_type = Bivariate

    def __init__(self, kde, **kwargs):
        super(BivariatePlot, self).__init__(kde, **kwargs)
        self.cyclic_range = self._stack.last.cyclic_range


    def __call__(self, axis=None, cyclic_index=0, lbrt=None):
        kdeview = self._stack.last
        self.style = View.options.style(kdeview)[cyclic_index]

        # Create xticks and reorder data if cyclic
        if lbrt is None:
            lbrt = kdeview.lbrt if self.rescale_individually else\
                   self._stack.lbrt

        if self.joint:
            if axis is not None:
                 raise Exception("Joint plots can't be animated or "
                                 "laid out in a grid.")
        else:
            self.ax = self._axis(axis, self._format_title(-1),
                                 kdeview.xlabel, kdeview.ylabel,
                                 lbrt=lbrt)

        self._update_plot(-1)

        if axis is None: plt.close(self.handles['fig'])
        return self.ax if axis else self.handles['fig']


    def _update_plot(self, n):
        kdeview = list(self._stack.values())[n]
        if self.joint:
            self.style.pop('cmap')
            self.handles['fig'] = sns.jointplot(kdeview.data[:,0],
                                                kdeview.data[:,1],
                                                **self.style).fig
        else:
            sns.kdeplot(kdeview.data, ax=self.ax,
                        zorder=self.zorder, **self.style)



class TimeSeriesPlot(SeabornPlot):
    """
    TimeSeries visualizes sets of curves using the Seaborn
    tsplot function. This provides functionality to plot
    error bars with various styles alongside the averaged
    curve.
    """

    rescale_individually = param.Boolean(default=False)

    show_frame = param.Boolean(default=False, doc="""
       Disabled by default for clarity.""")

    show_legend = param.Boolean(default=True, doc="""
      Whether to show legend for the plot.""")

    style_opts = param.List(default=['color', 'alpha', 'err_style',
                                     'interpolate', 'ci', 'n_boot',
                                     'err_kws', 'err_palette',
                                     'estimator', 'kwargs'],
                            constant=True, doc="""
       The style options for TimeSeriesPlot match those of seaborns
       tsplot.""")

    _stack_type = DataStack
    _view_type = TimeSeries

    def __init__(self, curves, **kwargs):
        super(TimeSeriesPlot, self).__init__(curves, **kwargs)
        self.cyclic_range = self._stack.last.cyclic_range


    def __call__(self, axis=None, cyclic_index=0, lbrt=None):
        curveview = self._stack.last
        self.cyclic_index = cyclic_index
        self.style = View.options.style(curveview)[self.cyclic_index]

        # Create xticks and reorder data if cyclic
        if lbrt is None:
            lbrt = None if self.rescale_individually else\
                   self._stack.lbrt

        self.ax = self._axis(axis, self._format_title(-1),
                             curveview.xlabel, curveview.ylabel,
                             lbrt=lbrt)

        self._update_plot(-1)

        if axis is None: plt.close(self.handles['fig'])
        return self.ax if axis else self.handles['fig']


    def _update_plot(self, n):
        curveview = list(self._stack.values())[n]
        sns.tsplot(curveview.data, curveview.xdata, ax=self.ax,
                   zorder=self.zorder, **self.style)



class DistributionPlot(SeabornPlot):
    """
    DistributionPlot visualizes Distribution Views using the
    Seaborn distplot function. This allows visualizing a 1D
    array as a histogram, kernel density estimate, or rugplot.
    """

    rescale_individually = param.Boolean(default=False)

    show_frame = param.Boolean(default=False, doc="""
       Disabled by default for clarity.""")

    style_opts = param.List(default=['bins', 'hist', 'kde', 'rug',
                                     'fit', 'hist_kws', 'kde_kws',
                                     'rug_kws', 'fit_kws', 'color'],
                            constant=True, doc="""
       The style options for CurvePlot match those of matplotlib's
       LineCollection object.""")

    _stack_type = DataStack
    _view_type = Distribution

    def __init__(self, dist, **kwargs):
        super(DistributionPlot, self).__init__(dist, **kwargs)
        self.cyclic_range = self._stack.last.cyclic_range


    def __call__(self, axis=None, cyclic_index=0, lbrt=None):
        distview = self._stack.last
        self.style = View.options.style(distview)[cyclic_index]

        # Create xticks and reorder data if cyclic
        self.ax = self._axis(axis, self._format_title(-1),
                             distview.xlabel, distview.ylabel)

        self._update_plot(-1)

        if axis is None: plt.close(self.handles['fig'])
        return self.ax if axis else self.handles['fig']


    def _update_plot(self, n):
        distview = list(self._stack.values())[n]
        sns.distplot(distview.data, ax=self.ax, **self.style)



class SNSFramePlot(DFrameViewPlot):
    """
    SNSFramePlot takes an SNSFrame as input and plots the
    contained data using the set plot_type. This largely mirrors
    the way DFramePlot works, however, since most Seaborn plot
    types plot one dimension against another it uses the x and y
    parameters, which can be set on the SNSFrame.
    """

    plot_type = param.ObjectSelector(default='corrplot',
                                     objects=['interact', 'regplot',
                                              'lmplot', 'corrplot'],
                                     doc="""
        Selects which Seaborn plot type to use, when visualizing the
        SNSFrame. The options that can be passed to the plot_type are
        defined in dframe_options.""")

    dframe_options = {'regplot':  RegressionPlot.style_opts,
                      'lmplot':   ['hue', 'col', 'row', 'palette',
                                   'sharex', 'dropna', 'legend'],
                      'corrplot': ['annot', 'sig_stars', 'sig_tail',
                                   'sig_corr', 'cmap', 'cmap_range',
                                   'cbar'],
                      'interact': ['filled', 'cmap', 'colorbar',
                                   'levels', 'logistic', 'contour_kws'
                                   'scatter_kws']
                      }

    def __call__(self, axis=None, cyclic_index=0, lbrt=None):
        dfview = self._stack.last
        composed = axis is not None
        multi_dim = len(dfview.dimensions) > 1

        if composed and multi_dim and self.plot_type == 'lmplot':
            raise Exception("Multiple %s plots cannot be composed."
                            % self.plot_type)

        title = None if self.zorder > 0 else self._format_title(-1)
        self.ax = self._axis(axis, title)

        # Process styles
        self.style = View.options.style(dfview)[cyclic_index]
        styles = self.style.keys()
        for k in styles:
            if k not in self.dframe_options[self.plot_type]:
                self.warning('Plot option %s does not apply '
                             'to %s plot type.' % (k, self.plot_type))
                self.style.pop(k)

        # Legacy fix for Pandas, can be removed for Pandas >0.14
        self._update_plot(dfview)

        if not axis:
            fig = self.handles.get('fig', plt.gcf())
            plt.close(fig)
        return self.ax if axis else self.handles.get('fig', plt.gcf())


    def _update_plot(self, dfview):
        if self.plot_type == 'regplot':
            sns.regplot(x=dfview.x, y=dfview.y, data=dfview.data,
                        ax=self.ax, **self.style)
        elif self.plot_type == 'interact':
            sns.interactplot(dfview.x, dfview.x2, dfview.y,
                             data=dfview.data, ax=self.ax, **self.style)
        elif self.plot_type == 'corrplot':
            sns.corrplot(dfview.data, ax=self.ax, **self.style)
        elif self.plot_type == 'lmplot':
            sns.lmplot(x=dfview.x, y=dfview.y, data=dfview.data,
                       ax=self.ax, **self.style)


Plot.defaults.update({TimeSeries: TimeSeriesPlot,
                      Bivariate: BivariatePlot,
                      Distribution: DistributionPlot,
                      Regression: RegressionPlot,
                      SNSFrame: SNSFramePlot})
