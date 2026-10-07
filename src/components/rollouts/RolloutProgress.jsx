export default function RolloutProgress() {
    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <div className="flex justify-between text-sm text-gray-400 mb-2">
                <span>Overall Progress</span>
                <span>25%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-4">
                <div className="bg-blue-500 h-4 rounded-full" style={{ width: '25%' }}></div>
            </div>
        </div>
    );
}