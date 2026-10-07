export default function ChangeCard({ status }) {
    return (
        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700 flex justify-between items-center hover:border-gray-500 transition-colors cursor-pointer">
            <div>
                <h3 className="font-semibold text-white">Upgrade Agent Model to GPT-4.5</h3>
                <p className="text-sm text-gray-400 mt-1">Affects 3 Workflows, 1 Solution</p>
            </div>
            <span className="px-3 py-1 bg-blue-900/50 text-blue-400 border border-blue-800 rounded text-sm font-medium">{status}</span>
        </div>
    );
}