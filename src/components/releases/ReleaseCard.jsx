export default function ReleaseCard({ name, status }) {
    return (
        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700 flex justify-between items-center hover:border-gray-500 cursor-pointer">
            <div>
                <h3 className="font-semibold text-white">{name}</h3>
                <p className="text-sm text-gray-400">AgentService • Env: Staging</p>
            </div>
            <span className="px-3 py-1 bg-gray-900 text-gray-300 border border-gray-700 rounded text-sm font-medium">{status}</span>
        </div>
    );
}