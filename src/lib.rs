use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{
    PyAny, PyBool, PyDict, PyFloat, PyFrozenSet, PyInt, PyList, PySet, PyString, PyTuple,
};
use serde_json::{Map, Number, Value};

const MAX_DEPTH: usize = 128;

#[pyfunction]
fn format_record(
    time_value: &Bound<'_, PyAny>,
    logger: &str,
    level: &str,
    message: &str,
    kv: &Bound<'_, PyAny>,
) -> PyResult<String> {
    let mut obj = Map::with_capacity(8);
    obj.insert("time".to_string(), py_to_json(time_value, 0)?);
    obj.insert("logger".to_string(), Value::String(logger.to_string()));
    obj.insert("level".to_string(), Value::String(level.to_string()));
    obj.insert("message".to_string(), Value::String(message.to_string()));

    merge_mapping(&mut obj, kv, 0)?;

    serde_json::to_string(&obj).map_err(|err| PyValueError::new_err(err.to_string()))
}

#[pyfunction]
fn dumps(value: &Bound<'_, PyAny>) -> PyResult<String> {
    let value = py_to_json(value, 0)?;
    serde_json::to_string(&value).map_err(|err| PyValueError::new_err(err.to_string()))
}

fn merge_mapping(
    out: &mut Map<String, Value>,
    value: &Bound<'_, PyAny>,
    depth: usize,
) -> PyResult<()> {
    if value.is_none() {
        return Ok(());
    }

    if let Ok(dict) = value.cast::<PyDict>() {
        for (key, item) in dict.iter() {
            out.insert(py_key_to_string(&key)?, py_to_json(&item, depth + 1)?);
        }
        return Ok(());
    }

    let items = value.call_method0("items")?;
    for pair in items.try_iter()? {
        let pair = pair?;
        let pair = pair.cast::<PyTuple>()?;
        if pair.len() != 2 {
            continue;
        }

        let key = pair.get_item(0)?;
        let item = pair.get_item(1)?;
        out.insert(py_key_to_string(&key)?, py_to_json(&item, depth + 1)?);
    }

    Ok(())
}

fn py_to_json(value: &Bound<'_, PyAny>, depth: usize) -> PyResult<Value> {
    if depth > MAX_DEPTH {
        return Err(PyValueError::new_err(
            "maximum JSON serialization depth exceeded",
        ));
    }

    if value.is_none() {
        return Ok(Value::Null);
    }

    if value.is_instance_of::<PyBool>() {
        return Ok(Value::Bool(value.extract::<bool>()?));
    }

    if value.is_instance_of::<PyInt>() {
        if let Ok(int_value) = value.extract::<i64>() {
            return Ok(Value::Number(Number::from(int_value)));
        }

        if let Ok(uint_value) = value.extract::<u64>() {
            return Ok(Value::Number(Number::from(uint_value)));
        }

        return Ok(Value::String(value.str()?.to_string()));
    }

    if value.is_instance_of::<PyFloat>() {
        let float_value = value.extract::<f64>()?;
        return Ok(Number::from_f64(float_value).map_or(Value::Null, Value::Number));
    }

    if value.is_instance_of::<PyString>() {
        return Ok(Value::String(value.extract::<String>()?));
    }

    if let Some(numpy_value) = try_numpy_to_json(value, depth)? {
        return Ok(numpy_value);
    }

    if let Ok(dict) = value.cast::<PyDict>() {
        let mut obj = Map::with_capacity(dict.len());
        for (key, item) in dict.iter() {
            obj.insert(py_key_to_string(&key)?, py_to_json(&item, depth + 1)?);
        }
        return Ok(Value::Object(obj));
    }

    if let Ok(list) = value.cast::<PyList>() {
        return list_to_json(list.iter(), depth);
    }

    if let Ok(tuple) = value.cast::<PyTuple>() {
        return list_to_json(tuple.iter(), depth);
    }

    if let Ok(set) = value.cast::<PySet>() {
        return list_to_json(set.iter(), depth);
    }

    if let Ok(frozen_set) = value.cast::<PyFrozenSet>() {
        return list_to_json(frozen_set.iter(), depth);
    }

    Ok(Value::String(value.str()?.to_string()))
}

fn try_numpy_to_json(value: &Bound<'_, PyAny>, depth: usize) -> PyResult<Option<Value>> {
    let type_obj = value.get_type();
    let module = type_obj
        .getattr("__module__")
        .and_then(|module| module.extract::<String>());

    if !matches!(module.as_deref(), Ok(module) if module.starts_with("numpy")) {
        return Ok(None);
    }

    let converted = value.call_method0("tolist")?;
    py_to_json(&converted, depth + 1).map(Some)
}

fn list_to_json<'py>(
    values: impl Iterator<Item = Bound<'py, PyAny>>,
    depth: usize,
) -> PyResult<Value> {
    let mut list = Vec::new();
    for item in values {
        list.push(py_to_json(&item, depth + 1)?);
    }
    Ok(Value::Array(list))
}

fn py_key_to_string(value: &Bound<'_, PyAny>) -> PyResult<String> {
    if value.is_instance_of::<PyString>() {
        return value.extract::<String>();
    }

    Ok(value.str()?.to_string())
}

#[pymodule(gil_used = false)]
fn _native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(format_record, m)?)?;
    m.add_function(wrap_pyfunction!(dumps, m)?)?;
    Ok(())
}
