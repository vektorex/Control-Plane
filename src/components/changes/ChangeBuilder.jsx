export default function ChangeBuilder() {
    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 space-y-4">
            <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Natural Language Description</label>
                <textarea className="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-white" rows="3" placeholder="E.g. Replace the GitHub security workflow's model with another approved model."></textarea>
            </div>
            <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">Parse Change Proposal</button>
        </div>
    );
}