Migrate from deprecated pointer.Int32() to generic ptr.To() API

Update all uses of pointer.Int32() to ptr.To[int32]() and pointer.Bool() to ptr.To()



Search hints:
- Look for imports of k8s.io/utils/pointer
- Find calls to pointer.Int32, pointer.Bool, pointer.String
- Search in pkg/apis/ and test files
