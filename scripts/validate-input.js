const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const inputPath = path.join(root, "inputs", "match_prediction.json");
const schemaPath = path.join(root, "inputs", "match_prediction.schema.json");

function readJson(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (error) {
    throw new Error(`Invalid JSON in ${filePath}: ${error.message}`);
  }
}

function validateString(data, key, min, max, errors) {
  if (typeof data[key] !== "string") {
    errors.push(`${key} must be a string`);
    return;
  }
  const value = data[key].trim();
  if (value.length < min || value.length > max) {
    errors.push(`${key} must be ${min}-${max} characters`);
  }
}

function validate(data, schema) {
  const errors = [];
  const allowedKeys = new Set(Object.keys(schema.properties));

  for (const key of schema.required) {
    if (!(key in data)) errors.push(`Missing required field: ${key}`);
  }

  for (const key of Object.keys(data)) {
    if (!allowedKeys.has(key)) errors.push(`Unexpected field: ${key}`);
  }

  if ("template" in data && data.template !== "prematch_prediction") {
    errors.push("template must be prematch_prediction");
  }

  validateString(data, "match", 3, 80, errors);
  validateString(data, "public_team", 1, 20, errors);
  validateString(data, "model_pick", 1, 20, errors);
  validateString(data, "cta", 5, 160, errors);

  if (!Number.isInteger(data.probability) || data.probability < 0 || data.probability > 100) {
    errors.push("probability must be an integer from 0 to 100");
  }

  if (!Array.isArray(data.reasons)) {
    errors.push("reasons must be an array");
  } else {
    if (data.reasons.length < 1 || data.reasons.length > 3) {
      errors.push("reasons must contain 1-3 items");
    }
    data.reasons.forEach((reason, index) => {
      if (typeof reason !== "string" || reason.trim().length < 3 || reason.trim().length > 80) {
        errors.push(`reasons[${index}] must be 3-80 characters`);
      }
    });
  }

  return errors;
}

try {
  const schema = readJson(schemaPath);
  const data = readJson(inputPath);
  const errors = validate(data, schema);

  if (errors.length > 0) {
    console.error("Input validation failed:");
    for (const error of errors) console.error(`- ${error}`);
    process.exit(1);
  }

  console.log("Input validation passed.");
} catch (error) {
  console.error(error.message);
  process.exit(1);
}
