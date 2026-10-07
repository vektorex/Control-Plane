export default function SensitivityView() {
    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 text-gray-400">
            <h3 className="text-white font-bold mb-4">Capacity Sensitivity</h3>
            <p>With current capacity (4 available engineers), Release C fits in Window A.</p>
            <p className="text-yellow-400 mt-2">Reducing capacity by one resource moves Release C to Window B (2-day delay).</p>
        </div>
    );
}