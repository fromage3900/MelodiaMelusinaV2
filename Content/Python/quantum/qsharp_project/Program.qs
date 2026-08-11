namespace QuantumGameplay.Experiment {
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Math;

    function CandidateScore(difficulty : Double, spacing : Double) : Double {
        let balance = 1.0 - AbsD(difficulty - 0.75);
        let spacingScore = 1.0 - AbsD(spacing - 0.55);
        return MaxD(0.0, balance * 0.6 + spacingScore * 0.4);
    }

    operation PickBestCandidate(difficultyA : Double, spacingA : Double, difficultyB : Double, spacingB : Double) : Result {
        let scoreA = CandidateScore(difficultyA, spacingA);
        let scoreB = CandidateScore(difficultyB, spacingB);

        if scoreA >= scoreB {
            return Zero;
        } else {
            return One;
        }
    }
}
