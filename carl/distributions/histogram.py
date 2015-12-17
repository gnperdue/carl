# -*- coding: utf-8 -*-
#
# Carl is free software; you can redistribute it and/or modify it
# under the terms of the Revised BSD License; see LICENSE file for
# more details.

import numpy as np

from itertools import product

from sklearn.base import BaseEstimator
from sklearn.utils import check_random_state


class Histogram(BaseEstimator):
    def __init__(self, bins=10, range=None, random_state=None):
        self.bins = bins
        self.range = range
        self.random_state = random_state

    def pdf(self, X):
        indices = []

        for j in range(X.shape[1]):
            indices.append(np.searchsorted(self.edges_[j],
                                           X[:, j],
                                           side="right") - 1)

        return self.histogram_[indices]

    def nnlf(self, X):
        return -np.log(self.pdf(X))

    def cdf(self, X):
        raise NotImplementedError

    def rvs(self, n_samples):
        rng = check_random_state(self.random_state)

        # Draw random bins with respect to their densities
        h = (self.histogram_ / self.histogram_.sum()).ravel()
        flat_indices = np.searchsorted(np.cumsum(h),
                                       rng.rand(n_samples),
                                       side="right")

        # Build bin corners
        indices = np.unravel_index(flat_indices, self.histogram_.shape)
        indices_end = [a + 1 for a in indices]
        shape = [len(d) for d in self.edges_] + [len(self.edges_)]
        corners = np.array(list(product(*self.edges_))).reshape(shape)

        # Draw uniformly within bins
        low = corners[indices]
        high = corners[indices_end]
        u = rng.rand(*low.shape)

        return low + u * (high - low)

    def fit(self, X, y=None, sample_weight=None):
        # Compute histogram and edges
        h, e = np.histogramdd(X, bins=self.bins, range=self.range,
                              weights=sample_weight, normed=True)

        # Add empty bins for out of bound samples
        for j in range(X.shape[1]):
            h = np.insert(h, 0, 0., axis=j)
            h = np.insert(h, h.shape[j], 0., axis=j)
            e[j] = np.insert(e[j], 0, -np.inf)
            e[j] = np.insert(e, len(e[j]), np.inf)

        self.histogram_ = h
        self.edges_ = e

        return self

    def score(self, X, y=None):
        return self.nnlf(X)