export default function DecisionFilters({ type }) {
    return (
        <div className="flex gap-4 items-center">
            <select className="bg-gray-800 border border-gray-700 text-white rounded p-2">
                <option>All Severities</option>
                <option>Critical</option>
                <option>High</option>
            </select>
            <select className="bg-gray-800 border border-gray-700 text-white rounded p-2">
                <option>All Domains</option>
                <option>Governance</option>
                <option>Security</option>
            </select>
        </div>
    );
}