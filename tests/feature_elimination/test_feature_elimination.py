from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
import pytest
import pandas as pd
from probatus.feature_elimination import ShapRFECV, EarlyStoppingShapRFECV
from probatus.utils import preprocess_labels
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import get_scorer
import os


@pytest.fixture(scope="function")
def X():
    """
    Fixture for X.
    """
    return pd.DataFrame(
        {"col_1": [1, 1, 1, 1, 1, 1, 1, 0], "col_2": [0, 0, 0, 0, 0, 0, 0, 1], "col_3": [1, 0, 1, 0, 1, 0, 1, 0]},
        index=[1, 2, 3, 4, 5, 6, 7, 8],
    )


@pytest.fixture(scope="function")
def y():
    """
    Fixture for y.
    """
    return pd.Series([1, 0, 1, 0, 1, 0, 1, 0], index=[1, 2, 3, 4, 5, 6, 7, 8])


def test_shap_rfe_randomized_search(X, y, capsys):
    """
    Test with RandomizedSearchCV.
    """
    clf = DecisionTreeClassifier(max_depth=1)
    param_grid = {"criterion": ["gini"], "min_samples_split": [1, 2]}
    search = RandomizedSearchCV(clf, param_grid, cv=2, n_iter=2)
    with pytest.warns(None) as record:

        shap_elimination = ShapRFECV(search, step=0.8, cv=2, scoring="roc_auc", n_jobs=4, random_state=1)
        report = shap_elimination.fit_compute(X, y)

    assert shap_elimination.fitted
    shap_elimination._check_if_fitted()

    assert report.shape[0] == 2
    assert shap_elimination.get_reduced_features_set(1) == ["col_3"]

    _ = shap_elimination.plot(show=False)

    # Ensure that number of warnings was at least 2 for the verbose (2 generated by probatus + possibly more by SHAP)
    assert len(record) >= 2

    # Check if there is any prints
    out, _ = capsys.readouterr()
    assert len(out) == 0


def test_shap_rfe(X, y, capsys):
    """
    Test with ShapRFECV.
    """
    clf = DecisionTreeClassifier(max_depth=1, random_state=1)
    with pytest.warns(None) as record:
        shap_elimination = ShapRFECV(
            clf,
            random_state=1,
            step=1,
            cv=2,
            scoring="roc_auc",
            n_jobs=4,
        )
        shap_elimination = shap_elimination.fit(X, y, approximate=True, check_additivity=False)

    assert shap_elimination.fitted
    shap_elimination._check_if_fitted()

    report = shap_elimination.compute()

    assert report.shape[0] == 3
    assert shap_elimination.get_reduced_features_set(1) == ["col_3"]

    _ = shap_elimination.plot(show=False)

    # Ensure that number of warnings was 0
    assert len(record) == 0
    # Check if there is any prints
    out, _ = capsys.readouterr()
    assert len(out) == 0


def test_shap_rfe_linear_model(X, y, capsys):
    """
    Test ShapRFECV with linear model.
    """
    clf = LogisticRegression(C=1, random_state=1)
    with pytest.warns(None) as record:
        shap_elimination = ShapRFECV(clf, random_state=1, step=1, cv=2, scoring="roc_auc", n_jobs=4)
        shap_elimination = shap_elimination.fit(X, y)

    assert shap_elimination.fitted
    shap_elimination._check_if_fitted()

    report = shap_elimination.compute()

    assert report.shape[0] == 3
    assert shap_elimination.get_reduced_features_set(1) == ["col_3"]

    _ = shap_elimination.plot(show=False)

    # Ensure that number of warnings was 0
    assert len(record) == 0
    # Check if there is any prints
    out, _ = capsys.readouterr()
    assert len(out) == 0


def test_shap_rfe_svm(X, y, capsys):
    """
    Test with ShapRFECV with SVM.
    """
    clf = SVC(C=1, kernel="linear", probability=True)
    with pytest.warns(None) as record:
        shap_elimination = ShapRFECV(clf, random_state=1, step=1, cv=2, scoring="roc_auc", n_jobs=4)
        shap_elimination = shap_elimination.fit(X, y)

    assert shap_elimination.fitted
    shap_elimination._check_if_fitted()

    report = shap_elimination.compute()

    assert report.shape[0] == 3
    assert shap_elimination.get_reduced_features_set(1) == ["col_3"]

    _ = shap_elimination.plot(show=False)

    # Ensure that number of warnings was 0
    assert len(record) == 0
    # Check if there is any prints
    out, _ = capsys.readouterr()
    assert len(out) == 0


def test_shap_rfe_cols_to_keep(X, y, capsys):
    """
    Test for shap_rfe_cv with feautures to keep parameter.
    """
    clf = DecisionTreeClassifier(max_depth=1, random_state=1)
    with pytest.warns(None) as record:
        shap_elimination = ShapRFECV(
            clf, random_state=1, step=2, cv=2, scoring="roc_auc", n_jobs=4, min_features_to_select=1
        )
        shap_elimination = shap_elimination.fit(X, y, columns_to_keep=["col_2", "col_3"])

    assert shap_elimination.fitted
    shap_elimination._check_if_fitted()

    report = shap_elimination.compute()

    assert report.shape[0] == 2
    reduced_feature_set = set(shap_elimination.get_reduced_features_set(num_features=2))
    assert reduced_feature_set == set(["col_2", "col_3"])

    # Ensure that number of warnings was 0
    assert len(record) == 0
    # Check if there is any prints
    out, _ = capsys.readouterr()
    assert len(out) == 0


def test_shap_rfe_randomized_search_cols_to_keep(X, y, capsys):
    """
    Test with ShapRFECV with column to keep param.
    """
    clf = DecisionTreeClassifier(max_depth=1)
    param_grid = {"criterion": ["gini"], "min_samples_split": [1, 2]}
    search = RandomizedSearchCV(clf, param_grid, cv=2, n_iter=2)
    with pytest.warns(None) as record:

        shap_elimination = ShapRFECV(search, step=0.8, cv=2, scoring="roc_auc", n_jobs=4, random_state=1)
        report = shap_elimination.fit_compute(X, y, columns_to_keep=["col_2", "col_3"])

    assert shap_elimination.fitted
    shap_elimination._check_if_fitted()

    assert report.shape[0] == 2
    reduced_feature_set = set(shap_elimination.get_reduced_features_set(num_features=2))
    assert reduced_feature_set == set(["col_2", "col_3"])

    _ = shap_elimination.plot(show=False)

    # Ensure that number of warnings was at least 2 for the verbose (2 generated by probatus + possibly more by SHAP)
    assert len(record) >= 2

    # Check if there is any prints
    out, _ = capsys.readouterr()
    assert len(out) == 0


def test_calculate_number_of_features_to_remove():
    """
    Test with ShapRFECV with n features to remove.
    """
    assert 3 == ShapRFECV._calculate_number_of_features_to_remove(
        current_num_of_features=10, num_features_to_remove=3, min_num_features_to_keep=5
    )
    assert 3 == ShapRFECV._calculate_number_of_features_to_remove(
        current_num_of_features=8, num_features_to_remove=5, min_num_features_to_keep=5
    )
    assert 0 == ShapRFECV._calculate_number_of_features_to_remove(
        current_num_of_features=5, num_features_to_remove=1, min_num_features_to_keep=5
    )
    assert 4 == ShapRFECV._calculate_number_of_features_to_remove(
        current_num_of_features=5, num_features_to_remove=7, min_num_features_to_keep=1
    )


def test_get_feature_shap_values_per_fold(X, y):
    """
    Test with ShapRFECV with features per fold.
    """
    clf = DecisionTreeClassifier(max_depth=1)
    shap_elimination = ShapRFECV(clf)
    shap_values, train_score, test_score = shap_elimination._get_feature_shap_values_per_fold(
        X, y, clf, train_index=[2, 3, 4, 5, 6, 7], val_index=[0, 1], scorer=get_scorer("roc_auc")
    )
    assert test_score == 1
    assert train_score > 0.9
    assert shap_values.shape == (2, 3)


@pytest.mark.skipif(os.environ.get("SKIP_LIGHTGBM") == "true", reason="LightGBM tests disabled")
def test_complex_dataset(complex_data, complex_lightgbm):
    """
    Test on complex dataset.
    """
    X, y = complex_data

    param_grid = {
        "n_estimators": [5, 7, 10],
        "num_leaves": [3, 5, 7, 10],
    }
    search = RandomizedSearchCV(complex_lightgbm, param_grid, n_iter=1)

    shap_elimination = ShapRFECV(clf=search, step=1, cv=10, scoring="roc_auc", n_jobs=3, verbose=50)
    with pytest.warns(None) as record:
        report = shap_elimination.fit_compute(X, y)

    assert report.shape[0] == X.shape[1]

    assert len(record) >= 2


@pytest.mark.skipif(os.environ.get("SKIP_LIGHTGBM") == "true", reason="LightGBM tests disabled")
def test_shap_rfe_early_stopping(complex_data, capsys):
    """
    Test EarlyStoppingShapRFECV with a LGBMClassifier.
    """
    from lightgbm import LGBMClassifier

    clf = LGBMClassifier(n_estimators=200, max_depth=3)
    X, y = complex_data

    with pytest.warns(None) as record:
        shap_elimination = EarlyStoppingShapRFECV(
            clf,
            random_state=1,
            step=1,
            cv=10,
            scoring="roc_auc",
            n_jobs=4,
            early_stopping_rounds=5,
            eval_metric="auc",
        )
        shap_elimination = shap_elimination.fit(X, y, approximate=True, check_additivity=False)

    assert shap_elimination.fitted
    shap_elimination._check_if_fitted()

    report = shap_elimination.compute()

    assert report.shape[0] == 5
    assert shap_elimination.get_reduced_features_set(1) == ["f5"]

    _ = shap_elimination.plot(show=False)

    # Ensure that number of warnings was 0
    assert len(record) == 0
    # Check if there is any prints
    out, _ = capsys.readouterr()
    assert len(out) == 0


@pytest.mark.skipif(os.environ.get("SKIP_LIGHTGBM") == "true", reason="LightGBM tests disabled")
def test_shap_rfe_randomized_search_early_stopping(complex_data):
    """
    Test EarlyStoppingShapRFECV with RandomizedSearchCV and a LGBMClassifier on complex dataset.
    """
    from lightgbm import LGBMClassifier

    clf = LGBMClassifier(n_estimators=200)
    X, y = complex_data

    param_grid = {
        "max_depth": [3, 4, 5],
    }
    search = RandomizedSearchCV(clf, param_grid, cv=2, n_iter=2)
    with pytest.warns(None) as record:
        shap_elimination = EarlyStoppingShapRFECV(
            search,
            step=1,
            cv=10,
            scoring="roc_auc",
            early_stopping_rounds=5,
            eval_metric="auc",
            n_jobs=4,
            verbose=50,
            random_state=1,
        )
        report = shap_elimination.fit_compute(X, y)

    assert shap_elimination.fitted
    shap_elimination._check_if_fitted()

    assert report.shape[0] == X.shape[1]
    assert shap_elimination.get_reduced_features_set(1) == ["f5"]

    _ = shap_elimination.plot(show=False)

    # Ensure that number of warnings was at least 3 for the verbose (2 generated by probatus + possibly more by SHAP)
    assert len(record) >= 3


@pytest.mark.skipif(os.environ.get("SKIP_LIGHTGBM") == "true", reason="LightGBM tests disabled")
def test_get_feature_shap_values_per_fold_early_stopping(complex_data):
    """
    Test with ShapRFECV with features per fold.
    """
    from lightgbm import LGBMClassifier

    clf = LGBMClassifier(n_estimators=200, max_depth=3)
    X, y = complex_data
    y = preprocess_labels(y, y_name="y", index=X.index)

    shap_elimination = EarlyStoppingShapRFECV(clf, early_stopping_rounds=5)
    shap_values, train_score, test_score = shap_elimination._get_feature_shap_values_per_fold(
        X,
        y,
        clf,
        train_index=list(range(5, 50)),
        val_index=[0, 1, 2, 3, 4],
        scorer=get_scorer("roc_auc"),
    )
    assert test_score > 0.6
    assert train_score > 0.6
    assert shap_values.shape == (5, 5)
