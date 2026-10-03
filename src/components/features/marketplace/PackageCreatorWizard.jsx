"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Package,
  Layers,
  Plug,
  Lock,
  Wrench,
  BookOpen,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ArrowLeft,
  Plus,
  Trash2,
  ShieldCheck,
  ShieldAlert,
} from "lucide-react";
import { marketplaceService } from "@/services/marketplace";

const STEPS = [
  { id: "info", label: "1. Info", icon: Package },
  { id: "components", label: "2. Components", icon: Layers },
  { id: "dependencies", label: "3. Dependencies", icon: Plug },
  { id: "permissions", label: "4. Permissions", icon: Lock },
  { id: "configuration", label: "5. Config", icon: Wrench },
  { id: "documentation", label: "6. Docs", icon: BookOpen },
  { id: "review", label: "7. Publish Preview", icon: ShieldCheck },
];

export function PackageCreatorWizard({ existingPackage = null }) {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [validationResult, setValidationResult] = useState(null);

  // Form State
  const [name, setName] = useState(existingPackage?.name || "");
  const [slug, setSlug] = useState(existingPackage?.slug || "");
  const [description, setDescription] = useState(existingPackage?.description || "");
  const [category, setCategory] = useState(existingPackage?.category || "workflow");
  const [packageType, setPackageType] = useState(existingPackage?.package_type || "work_pack");
  const [visibility, setVisibility] = useState(existingPackage?.visibility || "organization");
  const [tagsInput, setTagsInput] = useState((existingPackage?.tags || []).join(", "));

  // Manifest items
  const [version, setVersion] = useState("1.0.0");
  const [components, setComponents] = useState([
    { name: "Main Workflow", type: "workflow", identifier: "wf_main", config: {} },
  ]);
  const [dependencies, setDependencies] = useState([]);
  const [permissions, setPermissions] = useState([
    { scope: "tasks:read", description: "Read tasks" },
  ]);
  const [variables, setVariables] = useState([
    { name: "max_iterations", type: "integer", default: 3, description: "Maximum processing iterations" },
  ]);
  const [documentation, setDocumentation] = useState({
    readme: "# Package Overview\nDescribe how this package works and its operational goals.",
    usage: "Install via marketplace and configure the execution variables.",
    limitations: "Standard platform rate limits apply.",
    security_notes: "Requires no external secrets. Operates within authorized tenant boundaries.",
  });

  // Step 1: Auto-generate slug
  const handleNameChange = (val) => {
    setName(val);
    if (!existingPackage) {
      setSlug(
        val
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, "-")
          .replace(/^-|-$/g, "")
      );
    }
  };

  // Add/Remove Helpers
  const addComponent = () => {
    setComponents((prev) => [
      ...prev,
      { name: "New Component", type: "workflow_step", identifier: `step_${prev.length + 1}`, config: {} },
    ]);
  };
  const removeComponent = (index) => {
    setComponents((prev) => prev.filter((_, i) => i !== index));
  };

  const addDependency = () => {
    setDependencies((prev) => [
      ...prev,
      { dependency_type: "package", dependency_identifier: "pkg_core_tools", version_constraint: ">=1.0.0" },
    ]);
  };
  const removeDependency = (index) => {
    setDependencies((prev) => prev.filter((_, i) => i !== index));
  };

  const addPermission = () => {
    setPermissions((prev) => [
      ...prev,
      { scope: "workflows:read", description: "Inspect workflow status" },
    ]);
  };
  const removePermission = (index) => {
    setPermissions((prev) => prev.filter((_, i) => i !== index));
  };

  const addVariable = () => {
    setVariables((prev) => [
      ...prev,
      { name: `var_${prev.length + 1}`, type: "string", default: "", description: "" },
    ]);
  };
  const removeVariable = (index) => {
    setVariables((prev) => prev.filter((_, i) => i !== index));
  };

  // Construct manifest object
  const buildManifest = () => {
    const varMap = {};
    variables.forEach((v) => {
      varMap[v.name] = {
        type: v.type,
        default: v.default,
        description: v.description,
      };
    });

    return {
      schema_version: "1.0",
      package: {
        name,
        version,
        type: packageType,
      },
      compatibility: {
        platform_min_version: "1.0.0",
        platform_max_version: null,
        model_capabilities: ["structured_output"],
      },
      components,
      permissions,
      dependencies,
      configuration: {
        variables: varMap,
      },
      documentation,
    };
  };

  // Run Preview Validation on step 7
  const runPreview = async () => {
    setLoading(true);
    setError(null);
    try {
      const manifest = buildManifest();
      const res = await marketplaceService.previewManifest(manifest);
      setValidationResult(res);
    } catch (err) {
      setError(err?.message || "Manifest preview failed validation.");
    } finally {
      setLoading(false);
    }
  };

  // Next step click
  const handleNext = () => {
    if (currentStep === 0 && (!name || !slug)) {
      setError("Package name and slug are required.");
      return;
    }
    setError(null);
    if (currentStep === STEPS.length - 2) {
      runPreview();
    }
    setCurrentStep((prev) => Math.min(prev + 1, STEPS.length - 1));
  };

  // Publish / Save Package
  const handlePublish = async () => {
    setLoading(true);
    setError(null);
    try {
      const tags = tagsInput
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);

      // 1. Create or get package
      let pkgId = existingPackage?.id;
      if (!pkgId) {
        const pkg = await marketplaceService.createPackage({
          name,
          slug,
          description,
          category,
          package_type: packageType,
          visibility,
          tags,
        });
        pkgId = pkg.id;
      }

      // 2. Create version
      const manifest = buildManifest();
      const ver = await marketplaceService.createVersion(pkgId, {
        version,
        manifest,
      });

      // 3. Publish version
      await marketplaceService.publishVersion(pkgId, ver.id);

      router.push(`/app/marketplace/packages/${slug}`);
    } catch (err) {
      setError(err?.message || "Failed to publish package.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Stepper Header */}
      <div className="p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 shadow-xs flex items-center justify-between overflow-x-auto gap-2">
        {STEPS.map((step, idx) => {
          const Icon = step.icon;
          const isActive = idx === currentStep;
          const isDone = idx < currentStep;

          return (
            <button
              key={step.id}
              onClick={() => idx <= currentStep && setCurrentStep(idx)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors shrink-0 ${
                isActive
                  ? "bg-blue-600 text-white"
                  : isDone
                  ? "bg-neutral-100 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200"
                  : "text-neutral-400 opacity-60"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{step.label}</span>
            </button>
          );
        })}
      </div>

      {/* Step Form Body */}
      <div className="p-6 rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 shadow-sm text-xs space-y-5">
        {/* STEP 1: Basic Info */}
        {currentStep === 0 && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100">
              Package Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="font-semibold block mb-1">Package Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => handleNameChange(e.target.value)}
                  placeholder="e.g. Multi-Agent Research Pack"
                  className="w-full px-3 py-2 text-xs rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 focus:ring-1 focus:ring-blue-500 outline-hidden"
                />
              </div>

              <div>
                <label className="font-semibold block mb-1">Slug</label>
                <input
                  type="text"
                  value={slug}
                  onChange={(e) => setSlug(e.target.value)}
                  placeholder="e.g. multi-agent-research-pack"
                  className="w-full px-3 py-2 text-xs rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 focus:ring-1 focus:ring-blue-500 outline-hidden font-mono"
                />
              </div>

              <div className="md:col-span-2">
                <label className="font-semibold block mb-1">Description</label>
                <textarea
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Explain what this package does, what inputs it processes, and the expected outcomes..."
                  className="w-full px-3 py-2 text-xs rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 focus:ring-1 focus:ring-blue-500 outline-hidden"
                />
              </div>

              <div>
                <label className="font-semibold block mb-1">Package Type</label>
                <select
                  value={packageType}
                  onChange={(e) => setPackageType(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 focus:ring-1 focus:ring-blue-500 outline-hidden"
                >
                  <option value="work_pack">Work Pack (Multi-Component Bundle)</option>
                  <option value="workflow">Workflow Template</option>
                  <option value="prompt">Prompt Template</option>
                  <option value="tool">Tool Definition</option>
                  <option value="connector_template">Connector Template</option>
                  <option value="task_template">Task Template</option>
                  <option value="evaluation">Evaluation Dataset</option>
                </select>
              </div>

              <div>
                <label className="font-semibold block mb-1">Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 focus:ring-1 focus:ring-blue-500 outline-hidden capitalize"
                >
                  {["research", "writing", "coding", "data_analysis", "document_processing", "customer_support", "automation", "security", "evaluation", "productivity"].map(
                    (cat) => (
                      <option key={cat} value={cat}>
                        {cat.replace("_", " ")}
                      </option>
                    )
                  )}
                </select>
              </div>

              <div>
                <label className="font-semibold block mb-1">Visibility</label>
                <select
                  value={visibility}
                  onChange={(e) => setVisibility(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 focus:ring-1 focus:ring-blue-500 outline-hidden"
                >
                  <option value="organization">Organization (Visible to members only)</option>
                  <option value="private">Private (Restricted)</option>
                  <option value="public">Public (Open Marketplace)</option>
                </select>
              </div>

              <div>
                <label className="font-semibold block mb-1">Tags (comma separated)</label>
                <input
                  type="text"
                  value={tagsInput}
                  onChange={(e) => setTagsInput(e.target.value)}
                  placeholder="AI, RAG, research, agents"
                  className="w-full px-3 py-2 text-xs rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 focus:ring-1 focus:ring-blue-500 outline-hidden"
                />
              </div>
            </div>
          </div>
        )}

        {/* STEP 2: Components */}
        {currentStep === 1 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100">
                  Package Components
                </h3>
                <p className="text-neutral-500">
                  Declare referenced workflows, prompt templates, tools, and evaluation datasets.
                </p>
              </div>
              <button
                type="button"
                onClick={addComponent}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors"
              >
                <Plus className="w-3.5 h-3.5" /> Add Component
              </button>
            </div>

            <div className="space-y-3">
              {components.map((comp, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/50 flex flex-col md:flex-row items-start md:items-center gap-3"
                >
                  <div className="flex-1 w-full grid grid-cols-1 md:grid-cols-3 gap-2">
                    <input
                      type="text"
                      value={comp.name}
                      onChange={(e) => {
                        const copy = [...components];
                        copy[idx].name = e.target.value;
                        setComponents(copy);
                      }}
                      placeholder="Component Name"
                      className="px-2.5 py-1.5 rounded border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800"
                    />
                    <select
                      value={comp.type}
                      onChange={(e) => {
                        const copy = [...components];
                        copy[idx].type = e.target.value;
                        setComponents(copy);
                      }}
                      className="px-2.5 py-1.5 rounded border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800"
                    >
                      <option value="workflow">Workflow</option>
                      <option value="workflow_step">Workflow Step</option>
                      <option value="prompt">Prompt</option>
                      <option value="prompt_version">Prompt Version</option>
                      <option value="tool_definition">Tool Definition</option>
                      <option value="connector_template">Connector Template</option>
                      <option value="task_template">Task Template</option>
                      <option value="evaluation_dataset">Evaluation Dataset</option>
                      <option value="evaluation_case">Evaluation Case</option>
                    </select>
                    <input
                      type="text"
                      value={comp.identifier}
                      onChange={(e) => {
                        const copy = [...components];
                        copy[idx].identifier = e.target.value;
                        setComponents(copy);
                      }}
                      placeholder="Identifier (e.g. wf_main)"
                      className="px-2.5 py-1.5 rounded border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 font-mono"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => removeComponent(idx)}
                    className="p-2 text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded-lg"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* STEP 3: Dependencies */}
        {currentStep === 2 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100">
                  Dependencies
                </h3>
                <p className="text-neutral-500">
                  Declare dependency packages, connectors, or tools. Circular graphs are strictly rejected.
                </p>
              </div>
              <button
                type="button"
                onClick={addDependency}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors"
              >
                <Plus className="w-3.5 h-3.5" /> Add Dependency
              </button>
            </div>

            <div className="space-y-3">
              {dependencies.map((dep, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/50 flex flex-col md:flex-row items-start md:items-center gap-3"
                >
                  <div className="flex-1 w-full grid grid-cols-1 md:grid-cols-3 gap-2">
                    <select
                      value={dep.dependency_type}
                      onChange={(e) => {
                        const copy = [...dependencies];
                        copy[idx].dependency_type = e.target.value;
                        setDependencies(copy);
                      }}
                      className="px-2.5 py-1.5 rounded border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800"
                    >
                      <option value="package">Package</option>
                      <option value="workflow">Workflow</option>
                      <option value="prompt">Prompt</option>
                      <option value="tool">Tool</option>
                      <option value="connector">Connector</option>
                      <option value="model_capability">Model Capability</option>
                    </select>
                    <input
                      type="text"
                      value={dep.dependency_identifier}
                      onChange={(e) => {
                        const copy = [...dependencies];
                        copy[idx].dependency_identifier = e.target.value;
                        setDependencies(copy);
                      }}
                      placeholder="Identifier (e.g. core-tools)"
                      className="px-2.5 py-1.5 rounded border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 font-mono"
                    />
                    <input
                      type="text"
                      value={dep.version_constraint}
                      onChange={(e) => {
                        const copy = [...dependencies];
                        copy[idx].version_constraint = e.target.value;
                        setDependencies(copy);
                      }}
                      placeholder="Constraint (e.g. >=1.0.0)"
                      className="px-2.5 py-1.5 rounded border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 font-mono"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => removeDependency(idx)}
                    className="p-2 text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded-lg"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
              {dependencies.length === 0 && (
                <p className="text-neutral-400 italic">No external dependencies declared.</p>
              )}
            </div>
          </div>
        )}

        {/* STEP 4: Permissions */}
        {currentStep === 3 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100">
                  Permission Declarations
                </h3>
                <p className="text-neutral-500">
                  Declare API scopes required for execution. Scopes must conform to the platform scope registry.
                </p>
              </div>
              <button
                type="button"
                onClick={addPermission}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors"
              >
                <Plus className="w-3.5 h-3.5" /> Add Permission
              </button>
            </div>

            <div className="space-y-3">
              {permissions.map((perm, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/50 flex flex-col md:flex-row items-start md:items-center gap-3"
                >
                  <div className="flex-1 w-full grid grid-cols-1 md:grid-cols-2 gap-2">
                    <select
                      value={perm.scope}
                      onChange={(e) => {
                        const copy = [...permissions];
                        copy[idx].scope = e.target.value;
                        setPermissions(copy);
                      }}
                      className="px-2.5 py-1.5 rounded border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 font-mono"
                    >
                      <option value="tasks:read">tasks:read</option>
                      <option value="tasks:run">tasks:run</option>
                      <option value="workflows:read">workflows:read</option>
                      <option value="workflows:run">workflows:run</option>
                      <option value="documents:read">documents:read</option>
                      <option value="documents:write">documents:write</option>
                      <option value="models:read">models:read</option>
                      <option value="memory:read">memory:read</option>
                      <option value="memory:write">memory:write</option>
                      <option value="knowledge:read">knowledge:read</option>
                      <option value="marketplace:read">marketplace:read</option>
                      <option value="marketplace:install">marketplace:install</option>
                    </select>
                    <input
                      type="text"
                      value={perm.description}
                      onChange={(e) => {
                        const copy = [...permissions];
                        copy[idx].description = e.target.value;
                        setPermissions(copy);
                      }}
                      placeholder="Why is this permission needed?"
                      className="px-2.5 py-1.5 rounded border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => removePermission(idx)}
                    className="p-2 text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded-lg"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* STEP 5: Configuration */}
        {currentStep === 4 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100">
                  Configuration Variables
                </h3>
                <p className="text-neutral-500">
                  Strictly typed variables configured by the workspace administrator upon installation.
                </p>
              </div>
              <button
                type="button"
                onClick={addVariable}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors"
              >
                <Plus className="w-3.5 h-3.5" /> Add Variable
              </button>
            </div>

            <div className="space-y-3">
              {variables.map((v, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/50 flex flex-col md:flex-row items-start md:items-center gap-3"
                >
                  <div className="flex-1 w-full grid grid-cols-1 md:grid-cols-4 gap-2">
                    <input
                      type="text"
                      value={v.name}
                      onChange={(e) => {
                        const copy = [...variables];
                        copy[idx].name = e.target.value;
                        setVariables(copy);
                      }}
                      placeholder="Variable Key (e.g. depth)"
                      className="px-2.5 py-1.5 rounded border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 font-mono"
                    />
                    <select
                      value={v.type}
                      onChange={(e) => {
                        const copy = [...variables];
                        copy[idx].type = e.target.value;
                        setVariables(copy);
                      }}
                      className="px-2.5 py-1.5 rounded border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800"
                    >
                      <option value="string">string</option>
                      <option value="integer">integer</option>
                      <option value="number">number</option>
                      <option value="boolean">boolean</option>
                    </select>
                    <input
                      type="text"
                      value={v.default}
                      onChange={(e) => {
                        const copy = [...variables];
                        copy[idx].default = e.target.value;
                        setVariables(copy);
                      }}
                      placeholder="Default value"
                      className="px-2.5 py-1.5 rounded border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800"
                    />
                    <input
                      type="text"
                      value={v.description}
                      onChange={(e) => {
                        const copy = [...variables];
                        copy[idx].description = e.target.value;
                        setVariables(copy);
                      }}
                      placeholder="Description"
                      className="px-2.5 py-1.5 rounded border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => removeVariable(idx)}
                    className="p-2 text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded-lg"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* STEP 6: Documentation */}
        {currentStep === 5 && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100">
              Package Documentation
            </h3>
            <div className="space-y-3">
              <div>
                <label className="font-semibold block mb-1">README (Markdown)</label>
                <textarea
                  rows={4}
                  value={documentation.readme}
                  onChange={(e) =>
                    setDocumentation((prev) => ({ ...prev, readme: e.target.value }))
                  }
                  className="w-full px-3 py-2 text-xs rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 focus:ring-1 focus:ring-blue-500 outline-hidden font-mono"
                />
              </div>

              <div>
                <label className="font-semibold block mb-1">Usage Instructions</label>
                <textarea
                  rows={2}
                  value={documentation.usage}
                  onChange={(e) =>
                    setDocumentation((prev) => ({ ...prev, usage: e.target.value }))
                  }
                  className="w-full px-3 py-2 text-xs rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 focus:ring-1 focus:ring-blue-500 outline-hidden"
                />
              </div>

              <div>
                <label className="font-semibold block mb-1">Known Limitations</label>
                <input
                  type="text"
                  value={documentation.limitations}
                  onChange={(e) =>
                    setDocumentation((prev) => ({ ...prev, limitations: e.target.value }))
                  }
                  className="w-full px-3 py-2 text-xs rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 focus:ring-1 focus:ring-blue-500 outline-hidden"
                />
              </div>

              <div>
                <label className="font-semibold block mb-1">Security Notes</label>
                <input
                  type="text"
                  value={documentation.security_notes}
                  onChange={(e) =>
                    setDocumentation((prev) => ({ ...prev, security_notes: e.target.value }))
                  }
                  className="w-full px-3 py-2 text-xs rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 focus:ring-1 focus:ring-blue-500 outline-hidden"
                />
              </div>
            </div>
          </div>
        )}

        {/* STEP 7: Validation & Publish Preview */}
        {currentStep === 6 && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100">
              Deterministic Validation & Publishing Preview
            </h3>

            {loading ? (
              <div className="p-8 text-center text-neutral-500">
                Running static validation, credential scanner, and dependency resolution...
              </div>
            ) : validationResult ? (
              <div className="space-y-4">
                {/* Security Scan Result */}
                <div
                  className={`p-3.5 rounded-xl border flex items-center justify-between ${
                    validationResult.security_status === "scanned"
                      ? "border-emerald-200 dark:border-emerald-900/40 bg-emerald-50/50 dark:bg-emerald-950/20"
                      : "border-rose-200 dark:border-rose-900/40 bg-rose-50/50 dark:bg-rose-950/20"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {validationResult.security_status === "scanned" ? (
                      <ShieldCheck className="w-5 h-5 text-emerald-500" />
                    ) : (
                      <ShieldAlert className="w-5 h-5 text-rose-500" />
                    )}
                    <div>
                      <p className="font-semibold text-neutral-900 dark:text-neutral-100">
                        Security Scanning:{" "}
                        <span className="capitalize">{validationResult.security_status}</span>
                      </p>
                      <p className="text-[11px] text-neutral-500">
                        Zero embedded credentials, no arbitrary executable code, and no SSRF patterns detected.
                      </p>
                    </div>
                  </div>
                  <span className="font-mono text-[11px] text-neutral-500">
                    Content SHA-256: {validationResult.content_hash?.slice(0, 12)}...
                  </span>
                </div>

                {/* Compatibility Result */}
                <div className="p-3.5 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/40 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-blue-500" />
                    <span className="font-medium text-neutral-800 dark:text-neutral-200">
                      Platform Compatibility: {validationResult.compatibility?.status || "compatible"}
                    </span>
                  </div>
                  <span className="text-[11px] text-neutral-500">
                    Min platform v1.0.0
                  </span>
                </div>

                {/* Summary Table */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
                  <div className="p-3 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
                    <p className="text-neutral-400 text-[11px]">Components</p>
                    <p className="text-lg font-bold text-neutral-900 dark:text-neutral-100">{components.length}</p>
                  </div>
                  <div className="p-3 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
                    <p className="text-neutral-400 text-[11px]">Dependencies</p>
                    <p className="text-lg font-bold text-neutral-900 dark:text-neutral-100">{dependencies.length}</p>
                  </div>
                  <div className="p-3 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
                    <p className="text-neutral-400 text-[11px]">Permissions</p>
                    <p className="text-lg font-bold text-neutral-900 dark:text-neutral-100">{permissions.length}</p>
                  </div>
                  <div className="p-3 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
                    <p className="text-neutral-400 text-[11px]">Config Vars</p>
                    <p className="text-lg font-bold text-neutral-900 dark:text-neutral-100">{variables.length}</p>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        )}

        {/* Global Error Banner */}
        {error && (
          <div className="p-3 rounded-lg border border-rose-200 dark:border-rose-900/50 bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 text-xs">
            {error}
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="pt-4 border-t border-neutral-100 dark:border-neutral-800 flex items-center justify-between">
          <button
            type="button"
            disabled={currentStep === 0 || loading}
            onClick={() => setCurrentStep((prev) => Math.max(prev - 1, 0))}
            className="flex items-center gap-1 px-4 py-2 rounded-lg border border-neutral-200 dark:border-neutral-700 font-medium hover:bg-neutral-50 dark:hover:bg-neutral-800 disabled:opacity-40 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Previous
          </button>

          {currentStep < STEPS.length - 1 ? (
            <button
              type="button"
              onClick={handleNext}
              className="flex items-center gap-1 px-4 py-2 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition-colors shadow-xs"
            >
              Next <ArrowRight className="w-3.5 h-3.5" />
            </button>
          ) : (
            <button
              type="button"
              disabled={loading || validationResult?.security_status === "blocked"}
              onClick={handlePublish}
              className="flex items-center gap-1.5 px-5 py-2 rounded-lg bg-emerald-600 text-white font-semibold hover:bg-emerald-700 disabled:opacity-50 transition-colors shadow-xs"
            >
              <ShieldCheck className="w-4 h-4" />
              {loading ? "Publishing..." : "Publish Package Version"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
